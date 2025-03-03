import re
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import dateutil.parser


class ConversationManager:
    """Manager for appointment conversation flows."""
    
    def __init__(self, db):
        """Initialize with database access."""
        self.db = db
        self.current_appointment = None
        self.conversation_state = "initial"  # initial, confirming, rescheduling, completed
        self.proposed_times = []
        self.selected_time = None
    
    def set_appointment(self, appointment_data: Dict[str, Any]) -> None:
        """Set the current appointment for the conversation."""
        self.current_appointment = appointment_data
        self.conversation_state = "initial"
    
    def process_user_response(self, text: str) -> Dict[str, Any]:
        """Process a user response and update the conversation state."""
        text = text.lower()
        
        if self.conversation_state == "initial":
            # Check if the user wants to confirm or reschedule
            if any(word in text for word in ["yes", "confirm", "good", "fine", "okay", "sure", "correct"]):
                self.conversation_state = "confirming"
                return {
                    "intent": "confirm",
                    "response": "Great! I'll mark your appointment as confirmed. Is there anything else you need to know about your appointment?"
                }
            elif any(word in text for word in ["no", "reschedule", "change", "different", "can't make", "unable"]):
                self.conversation_state = "rescheduling"
                # Get available slots for the next week
                now = datetime.now()
                available_slots = self.db.get_available_slots(now, now + timedelta(days=7))
                
                # Format the available slots for conversation
                self.proposed_times = available_slots
                slot_texts = []
                for i, slot in enumerate(available_slots[:3]):  # Limit to 3 options
                    day = slot.strftime("%A, %B %d")
                    time = slot.strftime("%I:%M %p")
                    slot_texts.append(f"{day} at {time}")
                
                slots_text = ", ".join(slot_texts[:-1]) + " or " + slot_texts[-1] if len(slot_texts) > 1 else slot_texts[0]
                
                return {
                    "intent": "reschedule",
                    "response": f"I understand you'd like to reschedule. We have availability on {slots_text}. Would any of these times work for you?",
                    "available_slots": slot_texts
                }
            else:
                # Unclear response
                return {
                    "intent": "unclear",
                    "response": "I'm not sure if you want to confirm or reschedule your appointment. Can you please let me know if you'd like to keep your appointment or reschedule it?"
                }
        
        elif self.conversation_state == "confirming":
            # User has already confirmed, check if they have any questions
            if any(word in text for word in ["question", "ask", "wonder", "curious"]):
                return {
                    "intent": "question",
                    "response": "I'd be happy to help with any questions, but I don't have access to specific medical information. For medical questions, please speak with your doctor during your appointment. Is there anything else I can assist with regarding your appointment scheduling?"
                }
            else:
                # Assume they're done
                self.conversation_state = "completed"
                return {
                    "intent": "complete",
                    "response": "Thank you for confirming your appointment. We look forward to seeing you on " + 
                               f"{self.current_appointment.get('date', 'your scheduled date')} at " +
                               f"{self.current_appointment.get('time', 'your scheduled time')}. Have a great day!"
                }
        
        elif self.conversation_state == "rescheduling":
            # Try to identify which time slot the user prefers
            selected_index = None
            
            # Check for direct references to the options
            if "first" in text or "1st" in text or "option 1" in text or "option one" in text:
                selected_index = 0
            elif "second" in text or "2nd" in text or "option 2" in text or "option two" in text:
                selected_index = 1
            elif "third" in text or "3rd" in text or "option 3" in text or "option three" in text:
                selected_index = 2
            
            # Check for date/time mentions
            if selected_index is None:
                for i, slot in enumerate(self.proposed_times[:3]):
                    day = slot.strftime("%A").lower()
                    date = slot.strftime("%B %d").lower()
                    time = slot.strftime("%I:%M").lower()
                    hour = slot.strftime("%I").lower().lstrip('0')
                    ampm = slot.strftime("%p").lower()
                    
                    # Check for mentions of the day, date, or time
                    if day in text or date in text or time in text or f"{hour} {ampm}" in text:
                        selected_index = i
                        break
            
            if selected_index is not None and selected_index < len(self.proposed_times):
                self.selected_time = self.proposed_times[selected_index]
                self.conversation_state = "completed"
                
                # Format the selected time
                day = self.selected_time.strftime("%A, %B %d")
                time = self.selected_time.strftime("%I:%M %p")
                
                # Update the appointment in the database
                if self.current_appointment and 'appointment_id' in self.current_appointment:
                    appointment_id = self.current_appointment['appointment_id']
                    self.db.reschedule_appointment(appointment_id, self.selected_time)
                
                return {
                    "intent": "reschedule_confirmed",
                    "response": f"Great! I've rescheduled your appointment to {day} at {time}. You'll receive a confirmation message shortly. Is there anything else you need help with?",
                    "new_datetime": self.selected_time.isoformat()
                }
            else:
                # Couldn't identify a time preference
                return {
                    "intent": "unclear_time",
                    "response": "I'm sorry, I couldn't determine which time you prefer. Could you please specify which of the offered times works best for you?"
                }
        
        elif self.conversation_state == "completed":
            # Conversation is already completed
            if any(word in text for word in ["yes", "question", "help"]):
                return {
                    "intent": "additional_help",
                    "response": "For any other questions or concerns, please contact the office directly. Is there anything specific about your appointment that you'd like me to address?"
                }
            else:
                return {
                    "intent": "goodbye",
                    "response": "Thank you for your time. Have a wonderful day!"
                }
        
        # Default response
        return {
            "intent": "unknown",
            "response": "I'm not sure how to respond to that. Can you please clarify if you want to confirm or reschedule your appointment?"
        }
    
    def extract_date_time(self, text: str) -> Optional[datetime]:
        """Extract date and time from text using simple pattern matching."""
        # This is a simplified version - in a production system, you would use
        # a more sophisticated NLP approach or a dedicated library
        
        # Try to find date patterns like "May 15" or "May 15th"
        date_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* (\d+)(st|nd|rd|th)?', text.lower())
        
        # Try to find time patterns like "3 pm" or "3:30 pm"
        time_match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm)', text.lower())
        
        if not date_match and not time_match:
            return None
        
        # Current date/time as fallback
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = 9  # Default to 9 AM
        minute = 0
        
        # Extract date if found
        if date_match:
            month_str = date_match.group(1)
            month_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            month = month_map.get(month_str[:3], now.month)
            day = int(date_match.group(2))
        
        # Extract time if found
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or '0')
            ampm = time_match.group(3).lower()
            
            # Convert to 24-hour format
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
        
        # Create datetime object
        try:
            dt = datetime(year, month, day, hour, minute)
            
            # If the date is in the past, assume next year
            if dt < now:
                if month < now.month or (month == now.month and day < now.day):
                    dt = datetime(year + 1, month, day, hour, minute)
            
            return dt
        except ValueError:
            return None
    
    def get_conversation_state(self) -> str:
        """Get the current conversation state."""
        return self.conversation_state
    
    def get_conversation_outcome(self) -> Dict[str, Any]:
        """Get the outcome of the conversation."""
        if self.conversation_state == "completed":
            if self.selected_time:
                # Appointment was rescheduled
                return {
                    "outcome": "rescheduled",
                    "original_appointment": self.current_appointment,
                    "new_datetime": self.selected_time.isoformat()
                }
            else:
                # Appointment was confirmed
                return {
                    "outcome": "confirmed",
                    "appointment": self.current_appointment
                }
        else:
            # Conversation not completed
            return {
                "outcome": "incomplete",
                "state": self.conversation_state
            }
