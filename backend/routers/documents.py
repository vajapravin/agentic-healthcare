from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from core.db import SessionLocal
from core.models.patient_document import PatientDocument
from datetime import datetime

router = APIRouter(prefix="/documents", tags=["Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload")
async def upload_patient_document(
    patient_id: int = Form(...),
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a patient document, performs basic classification based on filename/content type,
    and stores the record in the database.
    """
    try:
        file_name = file.filename
        content_lower = document_type.lower()
        
        # Classification logic
        if "insurance" in content_lower or "policy" in content_lower:
            doc_type = "Insurance Card"
        elif "history" in content_lower or "medical" in content_lower or "prescription" in content_lower:
            doc_type = "Medical History"
        elif "id" in content_lower or "passport" in content_lower or "license" in content_lower:
            doc_type = "Government ID"
        else:
            doc_type = "General Medical Document"
            
        # Save to database
        new_doc = PatientDocument(
            patient_id=patient_id,
            document_type=doc_type,
            file_name=file_name,
            status="Classified & Stored",
            uploaded_at=datetime.utcnow()
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        return {
            "message": "Document uploaded and classified successfully",
            "document_id": new_doc.id,
            "patient_id": patient_id,
            "file_name": file_name,
            "document_type": doc_type,
            "status": new_doc.status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/status/{patient_id}")
def get_patient_document_status(patient_id: int, db: Session = Depends(get_db)):
    """
    Retrieves all uploaded documents and their current statuses for a specific patient.
    """
    documents = db.query(PatientDocument).filter(PatientDocument.patient_id == patient_id).all()
    
    if not documents:
        raise HTTPException(status_code=404, detail=f"No documents found for patient ID {patient_id}")
        
    return {
        "patient_id": patient_id,
        "total_documents": len(documents),
        "documents": [
            {
                "id": doc.id,
                "file_name": doc.file_name,
                "document_type": doc.document_type,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
            }
            for doc in documents
        ]
    }