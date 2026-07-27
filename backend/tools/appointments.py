from langchain.tools import tool
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
from core.db import SessionLocal
from core.models.appointment import Appointment
from core.models.department import Department
from core.models.doctor import Doctor
from core.models.patient_profile import PatientProfile
from core.logger import setup_logger

logger = setup_logger("appointment_tools")

@tool
def book_appointment(patient_id: int, start_time: str, department: str, doctor: str = None, end_time: str = None, reason: str = None) -> str:
    """
    Books an appointment for a patient. Patient ID, start time, and department are mandatory.
    If a doctor is omitted, an available doctor from the department will be automatically assigned.
    End time defaults to 30 minutes after start_time if omitted.
    
    Args:
        patient_id (int): The ID of the patient (Mandatory).
        start_time (str): The appointment start time in 'YYYY-MM-DD HH:MM:SS' format (Mandatory).
        department (str): The department for the appointment (Mandatory).
        doctor (str): The name of the doctor (Optional).
        end_time (str): Optional end time in 'YYYY-MM-DD HH:MM:SS'. Defaults to 30 minutes after start_time.
        reason (str): The medical reason or notes for the visit (Optional).

    Example:
        book_appointment(patient_id=1, start_time="2026-08-01 10:00:00", department="Cardiology", reason="Chest pain")
    """
    logger.info(f"locals: {locals()}")

    db = SessionLocal()
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        
        if not end_time:
            end_dt = start_dt + timedelta(minutes=30)
        else:
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        
        if start_dt >= end_dt:
            return "Error: Start time must be earlier than end time."

        # Appointments are limited to standard clinic hours.
        start_limit = datetime.strptime("10:00:00", "%H:%M:%S").time()
        end_limit = datetime.strptime("17:30:00", "%H:%M:%S").time()

        if not (start_limit <= start_dt.time() <= end_limit):
            return (
                "Error: Appointments can only be booked between 10:00 AM and "
                "5:30 PM."
            )

        patient_obj = (
            db.query(PatientProfile)
            .filter(PatientProfile.id == patient_id)
            .first()
        )
        if not patient_obj:
            return (
                f"Error: Patient ID {patient_id} does not exist in the "
                "database."
            )

        dept_obj = (
            db.query(Department)
            .filter(Department.name == department)
            .first()
        )
        if not dept_obj:
            return f"Error: Department '{department}' does not exist."

        if doctor:
            doctor_obj = (
                db.query(Doctor)
                .filter(
                    Doctor.name == doctor,
                    Doctor.department_id == dept_obj.id,
                )
                .first()
            )
            if not doctor_obj:
                return (
                    f"Error: Doctor '{doctor}' does not exist in department "
                    f"'{department}'."
                )

            doctor_conflict = db.query(Appointment).filter(
                Appointment.doctor_id == doctor_obj.id,
                Appointment.status == "booked",
                or_(
                    and_(
                        Appointment.start_time <= start_dt,
                        Appointment.end_time > start_dt,
                    ),
                    and_(
                        Appointment.start_time < end_dt,
                        Appointment.end_time >= end_dt,
                    ),
                    and_(
                        Appointment.start_time >= start_dt,
                        Appointment.end_time <= end_dt,
                    ),
                )
            ).first()

            if doctor_conflict:
                return (
                    f"Conflict Error: Doctor '{doctor_obj.name}' is already "
                    "booked during this time range."
                )
        else:
            # Automatically assign the first available doctor in the dept.
            department_doctors = (
                db.query(Doctor)
                .filter(Doctor.department_id == dept_obj.id)
                .all()
            )
            if not department_doctors:
                return (
                    f"Error: No doctors available under department "
                    f"'{department}'."
                )
            
            doctor_obj = None
            for doc in department_doctors:
                conflict = db.query(Appointment).filter(
                    Appointment.doctor_id == doc.id,
                    Appointment.status == "booked",
                    or_(
                        and_(
                            Appointment.start_time <= start_dt,
                            Appointment.end_time > start_dt,
                        ),
                        and_(
                            Appointment.start_time < end_dt,
                            Appointment.end_time >= end_dt,
                        ),
                        and_(
                            Appointment.start_time >= start_dt,
                            Appointment.end_time <= end_dt,
                        ),
                    )
                ).first()
                if not conflict:
                    doctor_obj = doc
                    break
            
            if not doctor_obj:
                return (
                    f"Conflict Error: All doctors in department "
                    f"'{department}' are fully booked during this time range."
                )

        patient_conflict = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.status == "booked",
            or_(
                and_(
                    Appointment.start_time <= start_dt,
                    Appointment.end_time > start_dt,
                ),
                and_(
                    Appointment.start_time < end_dt,
                    Appointment.end_time >= end_dt,
                ),
                and_(
                    Appointment.start_time >= start_dt,
                    Appointment.end_time <= end_dt,
                ),
            )
        ).first()

        if patient_conflict:
            return (
                f"Conflict Error: Patient ID {patient_id} already has an "
                "active overlapping appointment during this time."
            )

        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_obj.id,
            start_time=start_dt,
            end_time=end_dt,
            status="booked",
            reason=reason
        )

        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

        formatted_start = start_dt.strftime('%Y-%m-%d %H:%M')
        formatted_end = end_dt.strftime('%H:%M')

        return (
            f"Success: Appointment #{new_appointment.id} successfully booked "
            f"with Doctor '{doctor_obj.name}' ({dept_obj.name}) from "
            f"{formatted_start} to {formatted_end}."
        )

    except ValueError:
        return (
            "Error: Invalid date/time format. Please use "
            "'YYYY-MM-DD HH:MM:SS'."
        )
    except Exception as e:
        db.rollback()
        error_msg = f"Database error in book_appointment: {str(e)}"
        logger.error(error_msg)
        return error_msg
    finally:
        db.close()


@tool
def fetch_available_slots(
    department_name: str = None,
    date: str = None,
    doctor_name: str = None,
) -> str:
    """
    Retrieves available 30-minute appointment slots.
    
    Args:
        department_name (str): The name of the hospital department (Optional).
        date (str): The target date in YYYY-MM-DD format (Optional).
        doctor_name (str): The name of a specific doctor (Optional).

    Example:
        fetch_available_slots(department_name="General", date="2026-08-01")
    """
    logger.info(f"locals: {locals()}")

    try:
        db = SessionLocal()
        
        if department_name:
            dept = (
                db.query(Department)
                .filter(Department.name == department_name)
                .first()
            )
            if not dept:
                db.close()
                return (
                    f"Error: Department '{department_name}' does not exist in "
                    "the database."
                )

        doc_query = db.query(Doctor)
        if department_name:
            doc_query = doc_query.filter(Doctor.department_id == dept.id)
            
        if doctor_name:
            doctor_obj = (
                db.query(Doctor)
                .filter(Doctor.name == doctor_name)
                .first()
            )
            if not doctor_obj:
                db.close()
                return (
                    f"Error: Doctor '{doctor_name}' does not exist in the "
                    "database."
                )
            doc_query = doc_query.filter(Doctor.name == doctor_name)
            
        doctors = doc_query.all()
        if not doctors:
            db.close()
            return "No doctors found matching the specified criteria."

        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            target_date = datetime.utcnow().date()
        
        # Generate standard 30-minute slots for the clinic day.
        available_slots = []
        for doc in doctors:
            curr_time = datetime.combine(
                target_date, datetime.min.time()
            ).replace(hour=9)
            end_day_time = datetime.combine(
                target_date, datetime.min.time()
            ).replace(hour=17)
            
            while curr_time < end_day_time:
                slot_end = curr_time + timedelta(minutes=30)
                
                conflict = db.query(Appointment).filter(
                    Appointment.doctor_id == doc.id,
                    Appointment.status == "booked",
                    or_(
                        and_(
                            Appointment.start_time <= curr_time,
                            Appointment.end_time > curr_time,
                        ),
                        and_(
                            Appointment.start_time < slot_end,
                            Appointment.end_time >= slot_end,
                        ),
                        and_(
                            Appointment.start_time >= curr_time,
                            Appointment.end_time <= slot_end,
                        ),
                    )
                ).first()
                
                if not conflict and curr_time >= datetime.utcnow():
                    available_slots.append({
                        "doctor_name": doc.name,
                        "start_time": curr_time,
                        "end_time": slot_end
                    })
                
                curr_time = slot_end
                
        db.close()

        if not available_slots:
            return f"No available time slots found for date {target_date}."

        slot_summaries = [
            (
                f"Doctor: {slot['doctor_name']} | "
                f"{slot['start_time'].strftime('%Y-%m-%d %H:%M')} to "
                f"{slot['end_time'].strftime('%H:%M')}"
            )
            for slot in available_slots[:15]
        ]

        return (
            "Available appointment time slots:\n"
            + "\n".join(slot_summaries)
        )

    except ValueError:
        return "Error: Invalid date format. Please use YYYY-MM-DD."
    except Exception as e:
        logger.error(f"Error fetching slots: {str(e)}")
        return f"Error fetching slots: {str(e)}"


@tool
def cancel_appointment(appointment_id: int) -> str:
    """
    Cancels an existing appointment by its appointment ID.
    
    Args:
        appointment_id (int): The ID of the appointment to cancel.

    Example:
        cancel_appointment(appointment_id=4)
    """
    logger.info(f"locals: {locals()}")

    db = SessionLocal()
    try:
        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .first()
        )
        if not appointment:
            return (
                f"Error: Appointment ID {appointment_id} does not exist "
                "database."
            )
        
        appointment.status = "cancelled"
        db.commit()
        
        return f"Successfully canceled appointment ID {appointment_id}."
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error canceling appointment: {str(e)}")
        return f"Error canceling appointment: {str(e)}"
    finally:
        db.close()


@tool
def reschedule_appointment(
    appointment_id: int,
    new_start_time: str,
    new_end_time: str = None,
) -> str:
    """
    Updates an existing appointment after verifying doctor availability.
    
    Args:
        appointment_id (int): The ID of the appointment to reschedule.
        new_start_time (str): New start time in 'YYYY-MM-DD HH:MM:SS' format.
        new_end_time (str): Optional new end time in
            'YYYY-MM-DD HH:MM:SS'. Defaults to 30 mins after start.

    Example:
        reschedule_appointment(
            appointment_id=4,
            new_start_time="2026-08-02 14:00:00",
        )
    """
    logger.info(f"locals: {locals()}")
    
    db = SessionLocal()
    try:
        appointment = (
            db.query(Appointment)
            .filter(Appointment.id == appointment_id)
            .first()
        )
        if not appointment:
            return (
                f"Error: Appointment ID {appointment_id} does not exist in the "
                "database."
            )
        
        start_dt = datetime.strptime(new_start_time, "%Y-%m-%d %H:%M:%S")
        if not new_end_time:
            end_dt = start_dt + timedelta(minutes=30)
        else:
            end_dt = datetime.strptime(new_end_time, "%Y-%m-%d %H:%M:%S")

        if start_dt >= end_dt:
            return "Error: Start time must be earlier than end time."

        conflict = db.query(Appointment).filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.id != appointment_id,
            Appointment.status == "booked",
            or_(
                and_(
                    Appointment.start_time <= start_dt,
                    Appointment.end_time > start_dt,
                ),
                and_(
                    Appointment.start_time < end_dt,
                    Appointment.end_time >= end_dt,
                ),
                and_(
                    Appointment.start_time >= start_dt,
                    Appointment.end_time <= end_dt,
                ),
            )
        ).first()

        if conflict:
            return (
                "Conflict Error: The doctor is already booked during the "
                "requested time window."
            )

        appointment.start_time = start_dt
        appointment.end_time = end_dt
        db.commit()
        
        return (
            f"Successfully rescheduled appointment ID {appointment_id} to "
            f"{start_dt.strftime('%Y-%m-%d %H:%M')}."
        )
        
    except ValueError:
        return "Error: Invalid date/time format. Please use 'YYYY-MM-DD HH:MM:SS'."
    except Exception as e:
        db.rollback()
        logger.error(f"Error rescheduling appointment: {str(e)}")
        return f"Error rescheduling appointment: {str(e)}"
    finally:
        db.close()


@tool
def list_patient_appointments(patient_id: int) -> str:
    """
    Retrieves all active scheduled appointments for a specific patient.
    
    Args:
        patient_id (int): The ID of the patient whose appointments to list (Mandatory).

    Example:
        list_patient_appointments(patient_id=1)
    """
    logger.info(f"locals: {locals()}")

    db = SessionLocal()
    try:
        patient_obj = (
            db.query(PatientProfile)
            .filter(PatientProfile.id == patient_id)
            .first()
        )
        if not patient_obj:
            return (
                f"Error: Patient ID {patient_id} does not exist in the "
                "database."
            )

        appointments = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.status == "booked"
        ).all()
        
        if not appointments:
            return f"No active appointments found for Patient ID {patient_id}."
            
        appt_list = []
        for appt in appointments:
            doctor_name = appt.doctor.name if appt.doctor else "Unassigned"
            time_info = f"{appt.start_time.strftime('%Y-%m-%d %H:%M')} to {appt.end_time.strftime('%H:%M')}"
            appt_list.append(f"- ID: {appt.id} | Doctor: {doctor_name} | Time: {time_info}")
            
        return f"Active appointments for Patient ID {patient_id}:\n" + "\n".join(appt_list)
        
    except Exception as e:
        logger.error(f"Error retrieving patient appointments: {str(e)}")
        return f"Error retrieving patient appointments: {str(e)}"
    finally:
        db.close()