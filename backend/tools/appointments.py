from langchain.tools import tool
from sqlalchemy import cast, Date
from datetime import datetime, timedelta
from core.db import SessionLocal
from core.models.appointment import Appointment

@tool
def book_appointment(patient_id: int, department: str, scheduled_time: str) -> str:
    """
    Books an appointment for a patient in a specific hospital department.
    The scheduled_time must be in 'YYYY-MM-DD HH:MM:SS' format.
    """
    # Open a dedicated database session for this tool execution
    db = SessionLocal()
    try:
        # Convert the string from the LLM into a Python datetime object
        appt_time = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S')

        # Create a new appointment instance
        new_appointment = Appointment(
            patient_id=patient_id,
            department=department,
            scheduled_time=appt_time
        )

        # Add the new appointment to the database
        db.add(new_appointment)
        db.commit()
        db.refresh(new_appointment)

        return f"Success: Appointment booked #{new_appointment.id} booked in {department} at {scheduled_time}."

    except ValueError:
        return "Error: Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'."
    except Exception as e:
        db.rollback()
        error_msg = f"Error booking appointment: {str(e)}"
        # Add this print statement to expose the error in Docker logs
        print(f"\n--- DATABASE ERROR --- \n{error_msg}\n----------------------\n")
        return error_msg
    finally:
        # Always close the connection to prevent database lockups
        db.close()

@tool
def fetch_available_slots(department: str, date: str) -> str:
    """
    Retrieves available appointment times for a specific department on a given date.
    Date MUST be in YYYY-MM-DD format.
    """
    try:
        # 1. Parse the date string into a Python date object
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        db = SessionLocal()
        
        # 2. Query Supabase for all appointments in this department on this specific day
        booked_appointments = db.query(Appointment.scheduled_time).filter(
            Appointment.department == department,
            cast(Appointment.scheduled_time, Date) == target_date
        ).all()
        
        db.close()

        # Extract just the datetime objects from the SQL result
        print(f"Booked appointments for {department} on {date}: {booked_appointments}")
        booked_times = [app[0] for app in booked_appointments if app[0] is not None]

        # 3. Generate standard hourly slots (9:00 AM to 4:00 PM)
        available_slots = []
        for hour in range(9, 17):
            slot_time = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour)
            
            # If this time isn't in the database, it is available
            if slot_time not in booked_times:
                available_slots.append(slot_time.strftime("%Y-%m-%d %H:%M:%S"))

        if not available_slots:
            return f"No available slots for {department} on {date}."

        # 4. Return the next 3 available slots to keep the LLM response concise
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
        
        # Find the specific appointment
        appointment = db.query(Appointment).filter(
            Appointment.patient_id == patient_id,
            Appointment.department == department,
            cast(Appointment.scheduled_time, Date) == target_date
        ).first()
        
        if not appointment:
            db.close()
            return f"No appointment found for Patient ID {patient_id} in {department} on {date}."
        
        # Delete the appointment
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
    Directly updates an existing appointment to a new date and time. 
    Use this immediately when a user asks to reschedule, without checking available slots.
    """
    db = SessionLocal()
    try:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return f"Error: No appointment found with ID {appointment_id}."
        
        # Parse and update
        appointment.appointment_time = datetime.fromisoformat(new_slot)
        db.commit()
        
        return f"Successfully rescheduled appointment ID {appointment_id} to {new_slot}."
    except Exception as e:
        db.rollback()
        return f"Error rescheduling appointment: {str(e)}"
    finally:
        db.close()