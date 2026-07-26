from core.document_handler import check_missing_or_duplicate_documents
from langchain_core.tools import tool
from core.db import SessionLocal
from core.models.patient_document import PatientDocument
from langchain_core.runnables import RunnableConfig

@tool
def classify_and_store_document(patient_id: int, file_name: str, raw_text_content: str, config: RunnableConfig) -> str:
    """
    Classifies a patient-uploaded document (Insurance Card, Medical History, or ID) 
    and saves the classification record to the database.
    
    Args:
        patient_id (int): The ID of the patient owning the document.
        file_name (str): The name or descriptor of the uploaded file.
        raw_text_content (str): The extracted text or description of the document contents.
    """
    try:
        content_lower = raw_text_content.lower()
        
        # Simple keyword-based classification logic
        if "insurance" in content_lower or "policy" in content_lower or "coverage" in content_lower:
            doc_type = "Insurance Card"
        elif "history" in content_lower or "diagnosis" in content_lower or "prescription" in content_lower:
            doc_type = "Medical History"
        elif "id" in content_lower or "passport" in content_lower or "license" in content_lower:
            doc_type = "Government ID"
        else:
            doc_type = "General Medical Document"

        db = SessionLocal()

        # 1. Check for duplicate documents
        existing_doc = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id,
            PatientDocument.file_name == file_name,
            PatientDocument.document_type == doc_type
        ).first()
        
        if existing_doc:
            return f"Error: Duplicate document '{file_name}' of type '{doc_type}' already exists for patient ID {patient_id}."

        # 2. Utilize document_handler functions for validation
        audit_result = check_missing_or_duplicate_documents(existing_doc, file_name)
        
        doc_type_slug = audit_result["classified_type"]
        is_duplicate = audit_result["is_duplicate"]
        missing_docs = audit_result["missing_documents"]

        # Map slug back to readable database format
        type_mapping = {
            "insurance_card": "Insurance Card",
            "government_id": "Government ID",
            "medical_history": "Medical History",
            "unknown": "General Medical Document"
        }
        doc_type = type_mapping.get(doc_type_slug, "General Medical Document")

        # 3. Block duplicates
        if is_duplicate:
            db.close()
            return f"Error: Duplicate document '{file_name}' of type '{doc_type}' already exists for patient ID {patient_id}."

        # 4. Enforce Government ID mandate if missing
        if doc_type_slug != "government_id" and "government_id" in missing_docs:
            db.close()
            return f"Compliance Error: Cannot store {doc_type}. A valid Government ID is mandatory on file before other documents can be added for patient ID {patient_id}."
        
        new_doc = PatientDocument(
            patient_id=patient_id,
            document_type=doc_type,
            file_name=file_name,
            status="Classified & Verified"
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        db.close()
        
        return f"Document '{file_name}' successfully classified as '{doc_type}' and saved to patient record #{patient_id}."
        
    except Exception as e:
        return f"Error classifying and storing document: {str(e)}"

@tool
def extract_document_metadata():
    """
    Placeholder for a tool that would extract metadata from a document.
    This could include extracting dates, names, or other relevant information.
    """
    # Implementation would go here
    pass

@tool
def update_patient_record():
    """
    Placeholder for a tool that would update a patient's record based on the classified document.
    This could involve linking the document to the patient's profile or updating their medical history.
    """
    # Implementation would go here
    pass

@tool
def audit_required_forms():
    """
    Placeholder for a tool that would check if any required forms are missing or need to be audited.
    This could involve checking the patient's record for completeness.
    """
    # Implementation would go here
    pass