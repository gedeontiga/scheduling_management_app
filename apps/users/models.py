from django.utils import timezone
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    profile_picture = models.URLField(blank=True, null=True)
    
    # Required for authentication with Supabase and mobile app
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    device_tokens = models.JSONField(default=list, blank=True, null=True)
    
    # For offline sync
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(
        default=False,
        help_text="Designates whether this user should be treated as active. "
    )
    
    class Meta:
        models.Index(fields=['email']),
        models.Index(fields=['username']),
        
    def __str__(self):
        return self.username
    
class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return timezone.now() < self.expires_at
        
    def __str__(self):
        return f"Verification token for {self.user.email}"

class PasswordResetToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    def is_valid(self):
        return timezone.now() < self.expires_at
        
    def __str__(self):
        return f"Password reset token for {self.user.email}"