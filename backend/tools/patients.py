import re
from langchain_core.tools import tool
from core.db import SessionLocal
from core.models.user import User
from core.models.patient_profile import PatientProfile
from langchain_core.runnables import RunnableConfig

@tool
def register_patient(name: str, date_of_birth: str, phone: str = None, emergency_contact: str = None, config: RunnableConfig = None) -> str:
    """
    Registers a new patient in the database, creating both a User account and a PatientProfile.
    Both name and date_of_birth are mandatory fields.
    
    STRICT VALIDATION RULES:
    1. The name MUST be a valid human full name (e.g., 'Rakesh Bahl', 'Jane Doe'). 
    2. NEVER accept or pass generic placeholders, ID numbers, or strings like 'patient 119', 'user', or numbers as the patient's name. If the user provides a placeholder or ID instead of a real name, ask them to provide their actual full legal name before calling this tool.
    3. Automatically unmasks PII placeholder tokens (e.g., '<PERSON_1>') using the graph state mapping if the name was scrubbed by the safety node.
    
    Args:
        name (str): The valid full legal human name of the patient (Mandatory). Must never be an ID or placeholder string.
        date_of_birth (str): The patient's date of birth, strictly in 'YYYY-MM-DD' format (Mandatory).
        phone (str): The patient's phone number (Optional).
        emergency_contact (str): The emergency contact details (Optional).
    """
    db = SessionLocal()
    try:
        cleaned_name = name.strip()
        if re.search(r'(patient|user|client)\s*\d+', cleaned_name, re.IGNORECASE) or cleaned_name.isdigit():
            return f"Error: '{name}' is not a valid human name. Please provide the patient's actual full legal name (e.g., first and last name) before registering."

        # 2. Basic name format check
        if len(cleaned_name.split()) < 2 and not any(char.isalpha() for char in cleaned_name):
            return f"Error: '{name}' appears to be invalid. Please provide a full legal name containing letters."
        
        # Validate mandatory fields
        if not name or not name.strip() or not date_of_birth or not date_of_birth.strip():
            return "Error registering patient: Both 'name' and 'date_of_birth' are mandatory fields and cannot be empty."

        resolved_name = name.strip()
        resolved_dob = date_of_birth.strip()
        
        # Generate a unique synthetic email for the user account based on name
        email_slug = re.sub(r'[^a-z0-9]', '', resolved_name.lower())
        unique_email = f"{email_slug}_{int(datetime.utcnow().timestamp())}@patient.agentcare.local"

        # 1. Create User record first (since PatientProfile requires user_id)
        new_user = User(
            name=resolved_name,
            email=unique_email,
            role="patient"
        )
        db.add(new_user)
        db.flush() # Flushes to generate new_user.id without committing full transaction yet

        # 2. Create PatientProfile linked to the new User
        new_profile = PatientProfile(
            user_id=new_user.id,
            date_of_birth=resolved_dob,
            phone=phone,
            emergency_contact=emergency_contact
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        patient_id = new_profile.id
        db.close()
        
        return f"Successfully registered {resolved_name} (DOB: {resolved_dob}). Their new Patient Profile ID is {patient_id}."
        
    except Exception as e:
        db.rollback()
        db.close()
        return f"Error registering patient: {str(e)}"