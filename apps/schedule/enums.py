
from django.db import models

class StatusChoices(models.TextChoices):
    PENDING = 'Pending'
    ACCEPTED = 'Accepted'
    REJECTED = 'Rejected'
    CANCELLED = 'Cancelled'