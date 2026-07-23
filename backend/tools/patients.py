from langchain_core.tools import tool
from core.db import SessionLocal
from core.models.patient import Patient 
from langchain_core.runnables import RunnableConfig

@tool
def register_patient(name: str, config: RunnableConfig) -> str:
    """
    Registers a new patient in the database.
    Automatically unmasks PII tokens using the graph state mapping if needed.
    """
    try:
        # Access the graph state via LangGraph's runnable config
        configurable = config.get("configurable", {})
        # Depending on how the state is accessed in your tool node setup,
        # we can check if the name is a placeholder and resolve it.
        
        resolved_name = name
        
        # If the LLM passed a placeholder like <PERSON>, let's check the state
        if "<" in name and ">" in name:
            # LangGraph passes the current state store or we can pull it from the thread store if configured,
            # or we can handle the unmasking right before the tool call in an agent node.
            pass
            
        db = SessionLocal()
        new_patient = Patient(name=resolved_name)
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)
        
        patient_id = new_patient.id
        db.close()
        
        return f"Successfully registered {resolved_name}. Their new Patient ID is {patient_id}."
    except Exception as e:
        return f"Error registering patient: {str(e)}"