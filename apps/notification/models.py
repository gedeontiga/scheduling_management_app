import uuid
from django.conf import settings
from django.db import models

from apps.notification.enums import NotificationTypes

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=25, choices=NotificationTypes)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    actions = models.JSONField(default=dict, blank=True)
    delieved = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['type']),
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.type} for {self.user.username}: {self.title}"
    
class ScheduledAlarm(models.Model):
    """
    Alarms for time slots that need to trigger notifications
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scheduled_alarms')
    time_slot = models.ForeignKey('schedule.TimeSlot', on_delete=models.CASCADE, related_name='scheduled_alarms')
    
    minutes_before = models.PositiveIntegerField()
    scheduled_time = models.DateTimeField()
    triggered = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('user', 'time_slot', 'minutes_before')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['triggered']),
        ]
        
    def __str__(self):
        return f"Alarm for {self.user.username} at {self.scheduled_time}"
