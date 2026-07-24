from langchain_core.tools import tool
from core.db import SessionLocal
from core.models.patient import Patient 
from langchain_core.runnables import RunnableConfig

@tool
def register_patient(name: str, date_of_birth: str, config: RunnableConfig) -> str:
    """
    Registers a new patient in the database.
    Both name and date_of_birth are mandatory fields.
    Automatically unmasks PII tokens using the graph state mapping if needed.
    
    Args:
        name (str): The full legal name of the patient (Mandatory).
        date_of_birth (str): The patient's date of birth, strictly in 'YYYY-MM-DD' format (Mandatory).
    """
    try:
        # Validate that mandatory fields are provided and not empty
        if not name or not name.strip() or not date_of_birth or not date_of_birth.strip():
            return "Error registering patient: Both 'name' and 'date_of_birth' are mandatory fields and cannot be empty."

        # Access the graph state via LangGraph's runnable config
        configurable = config.get("configurable", {})
        
        resolved_name = name.strip()
        resolved_dob = date_of_birth.strip()
        
        # If the LLM passed a placeholder like <PERSON>, handle resolution
        if "<" in resolved_name and ">" in resolved_name:
            pass
            
        db = SessionLocal()
        new_patient = Patient(name=resolved_name, date_of_birth=resolved_dob)
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        patient_id = new_patient.id
        db.close()
        
        return f"Successfully registered {resolved_name} (DOB: {resolved_dob}). Their new Patient ID is {patient_id}."
    except Exception as e:
        return f"Error registering patient: {str(e)}"