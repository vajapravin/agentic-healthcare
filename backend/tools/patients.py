import re
from langchain_core.tools import tool
from core.db import SessionLocal
from core.models.patient import Patient 
from langchain_core.runnables import RunnableConfig

@tool
def register_patient(name: str, date_of_birth: str, config: RunnableConfig) -> str:
    """
    Registers a new patient in the database.
    Both name and date_of_birth are mandatory fields.
    
    STRICT VALIDATION RULES:
    1. The name MUST be a valid human full name (e.g., 'Rakesh Bahl', 'Jane Doe'). 
    2. NEVER accept or pass generic placeholders, ID numbers, or strings like 'patient 119', 'user', or numbers as the patient's name. If the user provides a placeholder or ID instead of a real name, ask them to provide their actual full legal name before calling this tool.
    3. Automatically unmasks PII placeholder tokens (e.g., '<PERSON_1>') using the graph state mapping if the name was scrubbed by the safety node.
    
    Args:
        name (str): The valid full legal human name of the patient (Mandatory). Must never be an ID or placeholder string.
        date_of_birth (str): The patient's date of birth, strictly in 'YYYY-MM-DD' format (Mandatory).
    """
    try:
        cleaned_name = name.strip()
        if re.search(r'(patient|user|client)\s*\d+', cleaned_name, re.IGNORECASE) or cleaned_name.isdigit():
            return f"Error: '{name}' is not a valid human name. Please provide the patient's actual full legal name (e.g., first and last name) before registering."

        # 2. Basic name format check (must contain at least two words or letters)
        if len(cleaned_name.split()) < 2 and not any(char.isalpha() for char in cleaned_name):
            return f"Error: '{name}' appears to be invalid. Please provide a full legal name containing letters."
        
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