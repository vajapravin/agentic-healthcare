from typing import List, Dict, Any

ALLOWED_DOCUMENT_TYPES = ["insurance_card", "government_id", "medical_history"]

def classify_document(file_name: str, file_content_summary: str) -> str:
    """
    Classifies incoming documents based on naming or metadata.
    """
    lower_name = file_name.lower()
    if "insurance" in lower_name:
        return "insurance_card"
    elif "id" in lower_name or "license" in lower_name or "passport" in lower_name:
        return "government_id"
    elif "history" in lower_name or "record" in lower_name:
        return "medical_history"
    return "unknown"

def check_missing_or_duplicate_documents(existing_docs: List[Dict[str, Any]], incoming_doc_name: str) -> Dict[str, Any]:
    """
    Checks for duplicates or missing mandatory files in the patient profile.
    """
    incoming_type = classify_document(incoming_doc_name, "")
    
    # Check for duplicates
    existing_types = [doc.get("type") for doc in existing_docs]
    is_duplicate = incoming_type in existing_types and incoming_type != "unknown"
    
    # Identify missing mandatory documents
    mandatory = {"insurance_card", "government_id"}
    collected_set = set(existing_types)
    if not is_duplicate and incoming_type != "unknown":
        collected_set.add(incoming_type)
        
    missing_docs = list(mandatory - collected_set)
    
    return {
        "classified_type": incoming_type,
        "is_duplicate": is_duplicate,
        "missing_documents": missing_docs
    }