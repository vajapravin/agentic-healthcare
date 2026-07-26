from langchain_core.tools import tool
from datetime import datetime
from core.db import SessionLocal
from core.models.reminder import Reminder

@tool
def schedule_reminder(patient_id: int, reminder_type: str, scheduled_at: str, appointment_id: int = None) -> str:
    """
    Schedules a notification reminder for a patient.
    
    Args:
        patient_id (int): The ID of the patient (Mandatory).
        reminder_type (str): The type of reminder (e.g., 'appointment_upcoming', 'document_required') (Mandatory).
        scheduled_at (str): The time to send the reminder in 'YYYY-MM-DD HH:MM:SS' format (Mandatory).
        appointment_id (int): The associated appointment ID if applicable (Optional).
    """
    db = SessionLocal()
    try:
        reminder_time = datetime.strptime(scheduled_at, '%Y-%m-%d %H:%M:%S')
        
        new_reminder = Reminder(
            patient_id=patient_id,
            appointment_id=appointment_id,
            reminder_type=reminder_type,
            scheduled_at=reminder_time,
            status="pending"
        )
        
        db.add(new_reminder)
        db.commit()
        db.refresh(new_reminder)
        db.close()
        
        return f"Success: Reminder #{new_reminder.id} scheduled for Patient ID {patient_id} at {scheduled_at}."
        
    except ValueError:
        return "Error: Invalid date/time format. Please use 'YYYY-MM-DD HH:MM:SS'."
    except Exception as e:
        db.rollback()
        db.close()
        return f"Error scheduling reminder: {str(e)}"