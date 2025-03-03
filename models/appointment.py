from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, timedelta
import uuid


class Appointment(BaseModel):
    """Appointment data model."""
    id: str
    patient_id: str
    doctor: str
    datetime: datetime
    duration: int = 30  # Duration in minutes
    status: Literal["scheduled", "confirmed", "cancelled", "rescheduled", "completed"] = "scheduled"
    notes: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class AppointmentDB:
    """Mock appointment database."""
    
    def __init__(self):
        """Initialize with some dummy data."""
        # Create some appointments for the next few days
        now = datetime.now()
        self.appointments = {
            "A001": Appointment(
                id="A001",
                patient_id="P001",
                doctor="Dr. Smith",
                datetime=now + timedelta(days=1, hours=2),
                status="scheduled",
            ),
            "A002": Appointment(
                id="A002",
                patient_id="P002",
                doctor="Dr. Johnson",
                datetime=now + timedelta(days=2, hours=4),
                status="scheduled",
            ),
        }
        
        # Available time slots (simplified for demo)
        self.available_slots = [
            now + timedelta(days=3, hours=9),  # 9 AM in 3 days
            now + timedelta(days=3, hours=10),  # 10 AM in 3 days
            now + timedelta(days=3, hours=14),  # 2 PM in 3 days
            now + timedelta(days=4, hours=11),  # 11 AM in 4 days
            now + timedelta(days=4, hours=15),  # 3 PM in 4 days
        ]
    
    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get an appointment by ID."""
        return self.appointments.get(appointment_id)
    
    def get_appointments_by_patient(self, patient_id: str) -> List[Appointment]:
        """Get all appointments for a patient."""
        return [
            appointment for appointment in self.appointments.values()
            if appointment.patient_id == patient_id
        ]
    
    def get_upcoming_appointments(self, patient_id: str) -> List[Appointment]:
        """Get upcoming appointments for a patient."""
        now = datetime.now()
        return [
            appointment for appointment in self.appointments.values()
            if appointment.patient_id == patient_id and appointment.datetime > now
        ]
    
    def add_appointment(self, appointment: Appointment) -> None:
        """Add an appointment to the database."""
        self.appointments[appointment.id] = appointment
    
    def update_appointment(self, appointment: Appointment) -> None:
        """Update an appointment in the database."""
        if appointment.id in self.appointments:
            self.appointments[appointment.id] = appointment
    
    def delete_appointment(self, appointment_id: str) -> None:
        """Delete an appointment from the database."""
        if appointment_id in self.appointments:
            del self.appointments[appointment_id]
    
    def confirm_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Confirm an appointment."""
        if appointment_id in self.appointments:
            self.appointments[appointment_id].status = "confirmed"
            return self.appointments[appointment_id]
        return None
    
    def reschedule_appointment(self, appointment_id: str, new_datetime: datetime) -> Optional[Appointment]:
        """Reschedule an appointment."""
        if appointment_id in self.appointments:
            self.appointments[appointment_id].datetime = new_datetime
            self.appointments[appointment_id].status = "rescheduled"
            return self.appointments[appointment_id]
        return None
    
    def get_available_slots(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Get available appointment slots within a date range."""
        return [
            slot for slot in self.available_slots
            if start_date <= slot <= end_date
        ]
    
    def is_slot_available(self, slot_datetime: datetime) -> bool:
        """Check if a time slot is available."""
        # In a real system, this would check against existing appointments
        return slot_datetime in self.available_slots
