
from django.db import models

class NotificationTypes(models.TextChoices):
    SCHEDULE_INVITATION = 'Schedule Invitation'
    PERMUTATION_REQUEST = 'Permutation Request'
    PERMUTATION_RESPONSE = 'Permutation Response'
    SCHEDULE_UPDATE = 'Schedule Update'
    ALARM = 'Appointment Alarm'
    SYSTEM = 'System Notification'