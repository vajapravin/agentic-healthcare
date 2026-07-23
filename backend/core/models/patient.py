from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from core.db import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date_of_birth = Column(String)
    is_active = Column(Boolean, default=True)

    # Note the string 'Appointment' to avoid circular imports
    appointments = relationship("Appointment", back_populates="patient")