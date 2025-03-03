from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Patient(BaseModel):
    """Patient data model."""
    id: str
    name: str
    phone_number: str
    email: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class PatientDB:
    """Mock patient database."""
    
    def __init__(self):
        """Initialize with some dummy data."""
        self.patients = {
            "P001": Patient(
                id="P001",
                name="John Doe",
                phone_number="+11234567890",
                email="john.doe@example.com",
            ),
            "P002": Patient(
                id="P002",
                name="Jane Smith",
                phone_number="+10987654321",
                email="jane.smith@example.com",
            ),
        }
    
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get a patient by ID."""
        return self.patients.get(patient_id)
    
    def get_patient_by_phone(self, phone_number: str) -> Optional[Patient]:
        """Get a patient by phone number."""
        for patient in self.patients.values():
            if patient.phone_number == phone_number:
                return patient
        return None
    
    def add_patient(self, patient: Patient) -> None:
        """Add a patient to the database."""
        self.patients[patient.id] = patient
    
    def update_patient(self, patient: Patient) -> None:
        """Update a patient in the database."""
        if patient.id in self.patients:
            self.patients[patient.id] = patient
    
    def delete_patient(self, patient_id: str) -> None:
        """Delete a patient from the database."""
        if patient_id in self.patients:
            del self.patients[patient_id]
