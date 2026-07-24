from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.db import Base

class PatientDocument(Base):
    __tablename__ = "patient_documents"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False)
    document_type = Column(String(50), nullable=False) # e.g., 'Insurance Card', 'Medical History', 'Government ID'
    file_name = Column(String(255), nullable=False)
    status = Column(String(50), default="Classified")
    uploaded_at = Column(DateTime, default=datetime.utcnow)