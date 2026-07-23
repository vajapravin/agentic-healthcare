from sqlalchemy.orm import Session
from langchain_core.tools import tool
from core.db import SessionLocal
# Assuming you have a Patient model defined similar to Appointment
from core.models.patient import Patient 

@tool
def register_patient(name: str) -> str:
    """
    Registers a new patient in the database.
    Requires the patient's full name.
    Returns a success message containing their new unique Patient ID.
    """
    try:
        db = SessionLocal()
        
        # Create a new Patient record
        new_patient = Patient(name=name)
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient) # This pulls the new auto-incremented ID back from Supabase
        
        patient_id = new_patient.id
        db.close()
        
        return f"Successfully registered {name}. Their new Patient ID is {patient_id}. Please provide this ID to the patient."
        
    except Exception as e:
        db.rollback()
        print(f"\n--- DATABASE ERROR --- \n{str(e)}\n----------------------\n")
        return f"Error registering patient: {str(e)}"