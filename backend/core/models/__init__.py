# Import Base so it is exposed when importing from core.models
from core.db import Base

# Import all models so they attach to Base.metadata
from .appointment import Appointment
from .audit_event import AuditEvent
from .department import Department
from .doctor import Doctor
from .escalation import Escalation
from .patient_document import PatientDocument
from .patient_profile import PatientProfile
from .reminder import Reminder
from .user import User
from .workflow_run import WorkflowRun

# This strictly defines what gets imported when someone runs `from core.models import *`
__all__ = ["Base", "Appointment", "AuditEvent", "Department", "Doctor", "Escalation", "PatientDocument", "PatientProfile", "Reminder", "User", "WorkflowRun"]