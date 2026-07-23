from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.db import Base
from datetime import datetime

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    department = Column(String, index=True)
    schedule_time = Column(DateTime)
    status = Column(String, default="booked")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to the Patient model
    patient = relationship("Patient", back_populates="appointments")