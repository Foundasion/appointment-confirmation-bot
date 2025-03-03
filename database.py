from .models.patient import Patient, PatientDB
from .models.appointment import Appointment, AppointmentDB
from datetime import datetime
from typing import List, Optional, Dict, Any


class Database:
    """Mock database interface that combines patient and appointment data."""
    
    def __init__(self):
        """Initialize the database with mock data."""
        self.patient_db = PatientDB()
        self.appointment_db = AppointmentDB()
    
    # Patient operations
    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get a patient by ID."""
        return self.patient_db.get_patient(patient_id)
    
    def get_patient_by_phone(self, phone_number: str) -> Optional[Patient]:
        """Get a patient by phone number."""
        return self.patient_db.get_patient_by_phone(phone_number)
    
    # Appointment operations
    def get_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Get an appointment by ID."""
        return self.appointment_db.get_appointment(appointment_id)
    
    def get_upcoming_appointments(self, patient_id: str) -> List[Appointment]:
        """Get upcoming appointments for a patient."""
        return self.appointment_db.get_upcoming_appointments(patient_id)
    
    def confirm_appointment(self, appointment_id: str) -> Optional[Appointment]:
        """Confirm an appointment."""
        return self.appointment_db.confirm_appointment(appointment_id)
    
    def reschedule_appointment(self, appointment_id: str, new_datetime: datetime) -> Optional[Appointment]:
        """Reschedule an appointment."""
        return self.appointment_db.reschedule_appointment(appointment_id, new_datetime)
    
    def get_available_slots(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """Get available appointment slots within a date range."""
        return self.appointment_db.get_available_slots(start_date, end_date)
    
    def is_slot_available(self, slot_datetime: datetime) -> bool:
        """Check if a time slot is available."""
        return self.appointment_db.is_slot_available(slot_datetime)
    
    def get_appointment_details(self, appointment_id: str) -> Dict[str, Any]:
        """Get detailed information about an appointment, including patient info."""
        appointment = self.get_appointment(appointment_id)
        if not appointment:
            return {}
        
        patient = self.get_patient(appointment.patient_id)
        if not patient:
            return {}
        
        # Format the appointment datetime for display
        formatted_date = appointment.datetime.strftime("%A, %B %d")
        formatted_time = appointment.datetime.strftime("%I:%M %p")
        
        return {
            "appointment_id": appointment.id,
            "patient_name": patient.name,
            "patient_phone": patient.phone_number,
            "doctor": appointment.doctor,
            "date": formatted_date,
            "time": formatted_time,
            "status": appointment.status,
            "duration": appointment.duration,
            "notes": appointment.notes,
        }
    
    def get_next_appointment_for_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get the next upcoming appointment for a patient by phone number."""
        patient = self.get_patient_by_phone(phone_number)
        if not patient:
            return None
        
        upcoming = self.get_upcoming_appointments(patient.id)
        if not upcoming:
            return None
        
        # Sort by datetime and get the earliest one
        next_appointment = sorted(upcoming, key=lambda a: a.datetime)[0]
        return self.get_appointment_details(next_appointment.id)
