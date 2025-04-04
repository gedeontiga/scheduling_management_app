import uuid
from django.conf import settings
from django.db import models

from apps.schedule.enums import StatusChoices

class Schedule(models.Model):
    # Existing fields...
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_schedules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    duration = models.PositiveIntegerField(help_text="Duration in Days", default=30)
    available_days = models.JSONField(default=dict)
    is_complete = models.BooleanField(default=False)
    
    min_days_selection = models.PositiveIntegerField(
        help_text="Minimum number of days each participant must select", 
        null=True, blank=True
    )
    user_specific_min_days = models.JSONField(
        default=dict, 
        help_text="User-specific minimum days requirements {user_id: min_days}"
    )
    
    def get_min_days_for_user(self, user_id):
        """Get minimum days requirement for a specific user or the default"""
        user_id_str = str(user_id)
        if user_id_str in self.user_specific_min_days:
            return self.user_specific_min_days[user_id_str]
        elif self.min_days_selection:
            return self.min_days_selection
        else:
            # Auto-calculate based on duration and participant count
            participant_count = self.participants.count()
            if participant_count > 0:
                return max(1, self.duration // (participant_count * 2))
            return 1
    
    class Meta:
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_complete']),
        ]
    
    @property
    def to_weeks(self):
        return self.duration // 7
    
    @property
    def to_months(self):
        return self.duration // 30
    
    @property
    def to_years(self):
        return self.duration // 365
    
    # @classmethod
    # def from_weeks(cls, name, weeks):
    #     """Factory method to create from weeks"""
    #     return cls(name=name, days_count=weeks*7)

    def __str__(self):
        return self.name
    
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    can_edit_schedule = models.BooleanField(default=False)
    can_invate_users = models.BooleanField(default=False)
    can_request_permutations = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('schedule', 'name')
        indexes = [
            models.Index(fields=['schedule']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.schedule.name})"
    
class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='participants')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='users')
    joined_at = models.DateTimeField(auto_now_add=True)
    invitation_accepted = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('schedule', 'user')
        indexes = [
            models.Index(fields=['schedule']),
            models.Index(fields=['user']),
            models.Index(fields=['invitation_accepted']),
        ]
        
    def __str__(self):
        return f"{self.user.username} in {self.schedule.name}"

class ScheduleDay(models.Model):
    """
    Represents a specific day in a schedule with participant availability
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    
    class Meta:
        unique_together = ('schedule', 'date')
        indexes = [
            models.Index(fields=['schedule', 'date']),
        ]
        
    def __str__(self):
        return f"{self.schedule.name} - {self.date}"
    
class TimeSlot(models.Model):
    """
    Represents a time slot within a schedule day that can be assigned to participants
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule_day = models.ForeignKey(ScheduleDay, on_delete=models.CASCADE, related_name='time_slots')
    start_time = models.TimeField()
    end_time = models.TimeField()
    participants = models.ManyToManyField(Participant, related_name='time_slots', blank=True)
    is_available = models.BooleanField(default=True)
    
    has_alarm = models.BooleanField(default=False)
    alarm_times = models.JSONField(default=list, blank=True)
    
    last_modified = models.DateTimeField(auto_now=True)
    sync_status = models.CharField(max_length=50, default='synced')
    
    class Meta:
        indexes = [
            models.Index(fields=['schedule_day']),
            models.Index(fields=['is_available']),
            models.Index(fields=['sync_status']),
        ]
        
    def __str__(self):
        return f"{self.schedule_day.date} - {self.start_time} to {self.end_time}"
    
class PermutationRequest(models.Model):
    """
    Request to switch time slots between participants
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='requested_permutations')
    recipient = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='received_permutations')
    requester_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='outgoing_permutation_requests')
    recipient_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name='incoming_permutation_requests')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=StatusChoices, default=StatusChoices.PENDING)
    
    class Meta:
        indexes = [
            models.Index(fields=['requester']),
            models.Index(fields=['recipient']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"Permutation between {self.requester.user.username} and {self.recipient.user.username}"