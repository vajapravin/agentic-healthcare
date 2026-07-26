from langchain.tools import tool
from sqlalchemy import cast, Date
from datetime import datetime, timedelta
from core.db import SessionLocal
from core.models.appointment import Appointment
from core.models.appointment_slot import AppointmentSlot
from core.models.department import Department

@tool
def book_appointment(patient_id: int, department_id: int, slot_id: int, doctor_id: int = None, reason: str = None) -> str:
    """
    Books an appointment for a patient using a specific appointment slot ID.
    All primary fields are mandatory, except doctor_id which is optional.
    
    Args:
        patient_id (int): The ID of the patient (Mandatory).
        department_id (int): The ID of the hospital department (Mandatory).
        slot_id (int): The ID of the specific appointment slot to book (Mandatory).
        doctor_id (int): The optional ID of the preferred doctor (Optional).
        reason (str): The medical reason or notes for the visit (Optional).
    """
    db = SessionLocal()
    try:
        # 1. Verify slot exists and is available
        slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
        if not slot:
            return f"Error: Appointment slot ID {slot_id} does not exist."
            
        if slot.status != "available" or slot.is_booked:
            return f"Conflict Error: Slot ID {slot_id} is already booked or unavailable."

        # 2. If a specific doctor_id was requested by the user, verify it matches the slot
        if doctor_id is not None and slot.doctor_id != doctor_id:
            return f"Conflict Error: Selected slot ID {slot_id} belongs to Doctor ID {slot.doctor_id}, not the requested Doctor ID {doctor_id}."

        # 3. Check if patient already has a conflicting booking at this exact time
        patient_conflict = db.query(Appointment).join(AppointmentSlot).filter(
            Appointment.patient_id == patient_id,
            AppointmentSlot.start_time == slot.start_time,
            Appointment.status == "booked"
        ).first()

        if patient_conflict:
            return f"Conflict Error: Patient ID {patient_id} already has another active appointment at {slot.start_time}."

        # 4. Book the appointment and lock the slot (use slot's doctor_id if optional doctor_id is omitted)
        assigned_doctor_id = doctor_id if doctor_id is not None else slot.doctor_id
        
        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_id=assigned_doctor_id,
            slot_id=slot_id,
            department_id=department_id,
            status="booked",
            reason=reason
        )
        
        slot.status = "booked"
        slot.is_booked = True

        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

        return f"Success: Appointment #{new_appointment.id} successfully booked for {slot.start_time} with Doctor ID {assigned_doctor_id}."

    except Exception as e:
        db.rollback()
        error_msg = f"Error booking appointment: {str(e)}"
        print(f"\n--- DATABASE ERROR --- \n{error_msg}\n----------------------\n")
        return error_msg
    finally:
        db.close()


@tool
def fetch_available_slots(department_id: int = None, date: str = None, doctor_id: int = None) -> str:
    """
    Retrieves available appointment slots based on any combination of department ID, date, or doctor ID.
    At least one parameter must be provided.
    
    Args:
        department_id (int): The ID of the hospital department (Optional).
        date (str): The target date in YYYY-MM-DD format (Optional).
        doctor_id (int): The ID of a specific doctor (Optional).
    """
    # Enforce that at least one parameter is provided
    if department_id is None and date is None and doctor_id is None:
        return "Error: Please provide at least one filter criterion (department_id, date, or doctor_id) to fetch available slots."

    try:
        db = SessionLocal()
        
        # Base query for available slots
        query = db.query(AppointmentSlot).filter(AppointmentSlot.status == "available")
        
        # Conditionally apply filters if provided
        if department_id is not None:
            query = query.filter(AppointmentSlot.department_id == department_id)
            
        if doctor_id is not None:
            query = query.filter(AppointmentSlot.doctor_id == doctor_id)
            
        if date is not None:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            query = query.filter(cast(AppointmentSlot.start_time, Date) == target_date)
            
        available_slots = query.order_by(AppointmentSlot.start_time.asc()).limit(15).all()
        db.close()

        if not available_slots:
            filters = []
            if department_id: filters.append(f"Department ID: {department_id}")
            if doctor_id: filters.append(f"Doctor ID: {doctor_id}")
            if date: filters.append(f"Date: {date}")
            filter_str = ", ".join(filters)
            return f"No available slots found matching [{filter_str}]."

        slot_summaries = [
            f"[Slot ID: {slot.id}] Dept #{slot.department_id} | Doctor #{slot.doctor_id} | {slot.start_time.strftime('%Y-%m-%d %H:%M')} to {slot.end_time.strftime('%H:%M')}"
            for slot in available_slots
        ]

        return "Available appointment slots matching your criteria:\n" + "\n".join(slot_summaries)

    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD."
    except Exception as e:
        print(f"\n--- DATABASE ERROR --- \n{str(e)}\n----------------------\n")
        return f"Error fetching slots: {str(e)}"

@tool
def cancel_appointment(appointment_id: int) -> str:
    """
    Cancels an existing appointment by its appointment ID, freeing up its slot.
    """
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        
        if not appointment:
            db.close()
            return f"No appointment found with ID {appointment_id}."
        
        # Free up the associated slot if it exists
        if appointment.slot_id:
            slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appointment.slot_id).first()
            if slot:
                slot.status = "available"
                slot.is_booked = False

        appointment.status = "cancelled"
        db.commit()
        db.close()
        
        return f"Successfully canceled appointment ID {appointment_id}."
        
    except Exception as e:
        db.rollback()
        print(f"\n--- DATABASE ERROR --- \n{str(e)}\n----------------------\n")
        return f"Error canceling appointment: {str(e)}"

@tool
def reschedule_appointment(appointment_id: int, new_slot_id: int) -> str:
    """
    Updates an existing appointment to a new slot ID after verifying slot availability.
    """
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return f"Error: No appointment found with ID {appointment_id}."
        
        new_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == new_slot_id).first()
        if not new_slot or new_slot.status != "available":
            return f"Conflict Error: Target slot ID {new_slot_id} is unavailable or does not exist."

        # Free old slot
        if appointment.slot_id:
            old_slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == appointment.slot_id).first()
            if old_slot:
                old_slot.status = "available"
                old_slot.is_booked = False

        # Assign new slot
        new_slot.status = "booked"
        new_slot.is_booked = True
        
        appointment.slot_id = new_slot_id
        appointment.doctor_id = new_slot.doctor_id
        appointment.department_id = new_slot.department_id
        
        db.commit()
        
        return f"Successfully rescheduled appointment ID {appointment_id} to {new_slot.start_time}."
    except Exception as e:
        db.rollback()
        return f"Error rescheduling appointment: {str(e)}"
    finally:
        db.close()

@tool
def list_patient_appointments(patient_id: int) -> str:
    """
    Retrieves all active scheduled appointments for a specific patient.
    
    Args:
        patient_id (int): The ID of the patient whose appointments to list (Mandatory).
    """
    db = SessionLocal()
    try:
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.status == "booked"
        ).all()
        
        if not appointments:
            return f"No active appointments found for Patient ID {patient_id}."
            
        appt_list = []
        for appt in appointments:
            slot_info = appt.slot.start_time.strftime('%Y-%m-%d %H:%M:%S') if appt.slot else "Unscheduled"
            appt_list.append(f"- ID: {appt.id} | Department ID: {appt.department_id} | Doctor ID: {appt.doctor_id} | Time: {slot_info}")
            
        return f"Active appointments for Patient ID {patient_id}:\n" + "\n".join(appt_list)
        
    except Exception as e:
        print(f"\n--- DATABASE ERROR --- \n{str(e)}\n----------------------\n")
        return f"Error retrieving patient appointments: {str(e)}"
    finally:
        db.close()