from langchain_core.tools import tool
from core.db import SessionLocal
from core.models.appointment import Appointment
from datetime import datetime

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