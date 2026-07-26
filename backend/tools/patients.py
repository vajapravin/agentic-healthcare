import re
from datetime import datetime
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
    2. NEVER accept or pass generic placeholders, ID numbers, or strings like 'patient 119', 'user', or numbers as the patient's name.
    
    Args:
        name (str): The valid full legal human name of the patient (Mandatory).
        date_of_birth (str): The patient's date of birth, strictly in 'YYYY-MM-DD' format (Mandatory).
        phone (str): The patient's phone number (Optional).
        emergency_contact (str): The emergency contact details (Optional).
    """
    db = SessionLocal()
    try:
        cleaned_name = name.strip()
        if re.search(r'(patient|user|client)\s*\d+', cleaned_name, re.IGNORECASE) or cleaned_name.isdigit():
            return f"Error: '{name}' is not a valid human name. Please provide the patient's actual full legal name."

        if len(cleaned_name.split()) < 2 and not any(char.isalpha() for char in cleaned_name):
            return f"Error: '{name}' appears to be invalid. Please provide a full legal name containing letters."
        
        if not name or not name.strip() or not date_of_birth or not date_of_birth.strip():
            return "Error registering patient: Both 'name' and 'date_of_birth' are mandatory fields and cannot be empty."

        resolved_name = name.strip()
        resolved_dob = date_of_birth.strip()
        
        # Generate a unique synthetic email for the user account based on name
        email_slug = re.sub(r'[^a-z0-9]', '', resolved_name.lower())
        unique_email = f"{email_slug}_{int(datetime.utcnow().timestamp())}@patient.agentcare.local"

        # 1. Create User record
        new_user = User(
            name=resolved_name,
            email=unique_email,
            role="patient"
        )
        db.add(new_user)
        db.flush()

        # 2. Create PatientProfile linked to User
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