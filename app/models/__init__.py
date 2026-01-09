# Импортируй ВСЕ модели здесь, чтобы Alembic видел Base.metadata
from .users import User, DoctorPatient
from .profiles import PatientProfile
from .allergy import PatientAllergy, patient_allergen, patient_symptom
from .asit import AsitPlan, AsitEvent
from .meds import PatientMedication, MedicationIntakeLog
from .reminders import Reminder
