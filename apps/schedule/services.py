
from django.db.models import Count

from apps.schedule.models import TimeSlot

class ScheduleValidationService:
    @staticmethod
    def validate_participant_selections(schedule, participant):
        """
        Validate that a participant has selected the minimum required days
        
        Returns:
            tuple: (is_valid, message)
        """
        # Get time slots where this participant is assigned
        participant_slots = TimeSlot.objects.filter(participants=participant)
        
        # Count unique days
        unique_days = participant_slots.values('schedule_day__date').distinct().count()
        
        # Check custom requirement for this participant
        custom_requirement = schedule.min_days_per_participant.get(str(participant.id))
        
        if custom_requirement:
            min_required = int(custom_requirement)
        else:
            min_required = schedule.min_days_required
            
        if unique_days < min_required:
            return (False, f"You must select at least {min_required} days")
        
        return (True, "Valid selection")
        
    @staticmethod
    def calculate_default_min_days(schedule):
        """
        Calculate sensible default for minimum days based on 
        schedule duration and number of participants
        """
        participant_count = schedule.participants.count()
        
        if participant_count == 0:
            return 1
            
        # Logic: at least 10% of schedule duration, 
        # divided by number of participants
        # with a minimum of 1 day
        min_days = max(1, int(schedule.duration * 0.1 / participant_count))
        
        return min_days