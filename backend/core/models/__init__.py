# Import Base so it is exposed when importing from core.models
from core.db import Base

# Import all models so they attach to Base.metadata
from .patient import Patient
from .appointment import Appointment

# This strictly defines what gets imported when someone runs `from core.models import *`
__all__ = ["Base", "Patient", "Appointment"]