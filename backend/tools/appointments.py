from langchain.tools import tool
from sqlalchemy import cast, Date
from datetime import datetime, timedelta
from core.db import SessionLocal
from core.models.appointment import Appointment

@tool
def book_appointment(patient_id: int, department: str, scheduled_time: str) -> str:
    """
        Books an appointment for a patient in a specific hospital department.
        All fields are mandatory. The patient_id must correspond to an existing patient in the database.
        The scheduled_time must be in 'YYYY-MM-DD HH:MM:SS' format.
        
        CRITICAL CONFLICT RULES:
        1. A patient cannot have multiple appointments in the same department.
        2. A patient cannot have overlapping time conflicts (two appointments at the exact same scheduled_time across any department).
        3. The department cannot be double-booked at the requested scheduled_time by any other patient.

        Args:
            patient_id (int): The ID of the patient for whom to book the appointment (Mandatory).
            department (str): The hospital department for the appointment (Mandatory). Must not already have an active appointment for this patient.
            scheduled_time (str): The time for the appointment in 'YYYY-MM-DD HH:MM:SS' format (Mandatory). Must be in the future and strictly avoid time conflicts with existing department or patient bookings.
        """
    db = SessionLocal()
    try:
        # Convert the string from the LLM into a Python datetime object
        appt_time = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')

        # 1. Validation: Ensure appointment is in the future
        if appt_time <= datetime.now():
            return "Error: Cannot book an appointment in the past. Please choose a future time slot."

        # 2. Conflict Check A: Check if the Department is already booked
        department_conflict = db.query(Appointment).filter(
            Appointment.department == department
        ).first()

        if department_conflict:
            return f"Conflict Error: The {department} department is already booked at {scheduled_time}. Please choose another slot."

        # 3. Conflict Check B: Check if the Patient already has an appointment anywhere at this exact time
        patient_conflict = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.scheduled_time == appt_time
        ).first()

        if patient_conflict:
            return f"Conflict Error: Patient ID {patient_id} already has an appointment booked in the '{patient_conflict.department}' department at {scheduled_time}, Appointment ID: {patient_conflict.id}."

        # 4. Create and commit the new appointment if no conflicts exist
        new_appointment = Appointment(
            patient_id=patient_id,
            department=department,
            scheduled_time=appt_time
        )

        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

        return f"Success: Appointment #{new_appointment.id} booked in {department} at {scheduled_time}."

    except ValueError:
        return "Error: Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'."
    except Exception as e:
        db.rollback()
        error_msg = f"Error booking appointment: {str(e)}"
        print(f"\n--- DATABASE ERROR --- \n{error_msg}\n----------------------\n")
        return error_msg
    finally:
        db.close()

@tool
def fetch_available_slots(department: str, date: str) -> str:
    """
    Retrieves available appointment times for a specific department on a given date.
    Date MUST be in YYYY-MM-DD format.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        db = SessionLocal()
        
        booked_appointments = db.query(Appointment.scheduled_time).filter(
            Appointment.department == department,
            cast(Appointment.scheduled_time, Date) == target_date
        ).all()
        
        db.close()

        booked_times = [app[0] for app in booked_appointments if app[0] is not None]

        available_slots = []
        for hour in range(9, 17):
            slot_time = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour)
            
            if slot_time not in booked_times:
                available_slots.append(slot_time.strftime("%Y-%m-%d %H:%M:%S"))

        if not available_slots:
            return f"No available slots for {department} on {date}."

        return f"Available slots for {department} on {date}: " + ", ".join(available_slots[:3])

    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD."
    except Exception as e:
        print(f"\n--- DATABASE ERROR --- \n{str(e)}\n----------------------\n")
        return f"Error fetching slots: {str(e)}"

@tool
def cancel_appointment(patient_id: int, department: str, date: str) -> str:
    """
    Cancels an existing appointment for a specific patient, department, and date.
    Date MUST be in YYYY-MM-DD format.
    """
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        db = SessionLocal()
        
        appointment = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.department == department,
            cast(Appointment.scheduled_time, Date) == target_date
        ).first()
        
        if not appointment:
            db.close()
            return f"No appointment found for Patient ID {patient_id} in {department} on {date}."
        
        db.delete(appointment)
        db.commit()
        db.close()
        
        return f"Successfully canceled the {department} appointment for Patient ID {patient_id} on {date}."
        
    except Exception as e:
        db.rollback()
        print(f"\n--- DATABASE ERROR --- \n{str(e)}\n----------------------\n")
        return f"Error canceling appointment: {str(e)}"

@tool
def reschedule_appointment(appointment_id: int, new_slot: str) -> str:
    """
    Directly updates an existing appointment to a new date and time after checking conflicts. 
    """
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return f"Error: No appointment found with ID {appointment_id}."
        
        new_time = datetime.strptime(new_slot, '%Y-%m-%d %H:%M:%S')

        # Check department conflict for the new slot (excluding the current appointment itself)
        dept_conflict = db.query(Appointment).filter(
            Appointment.department == appointment.department,
            Appointment.scheduled_time == new_time,
            Appointment.id != appointment_id
        ).first()

        if dept_conflict:
            return f"Conflict Error: The {appointment.department} department is already booked at {new_slot}."

        # Update and save
        appointment.scheduled_time = new_time
        db.commit()
        
        return f"Successfully rescheduled appointment ID {appointment_id} to {new_slot}."
    except ValueError:
        return "Error: Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'."
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
        # Query all appointments for the given patient ID, ordered by time
        appointments = db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(Appointment.scheduled_time.asc()).all()
        
        if not appointments:
            return f"No active appointments found for Patient ID {patient_id}."
            
        # Format the results into a clean, readable string for the agent/user
        appt_list = []
        for appt in appointments:
            time_str = appt.scheduled_time.strftime('%Y-%m-%d %H:%M:%S') if appt.scheduled_time else "Unscheduled"
            appt_list.append(f"- ID: {appt.id} | Department: {appt.department} | Time: {time_str}")
            
        return f"Active appointments for Patient ID {patient_id}:\n" + "\n".join(appt_list)
        
    except Exception as e:
        print(f"\n--- DATABASE ERROR --- \n{str(e)}\n----------------------\n")
        return f"Error retrieving patient appointments: {str(e)}"
    finally:
        db.close()