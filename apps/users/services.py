from django.core.mail import send_mail
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import datetime

from apps.users.models import EmailVerificationToken, PasswordResetToken
from config import settings

class EmailVerificationService:
    @staticmethod
    def create_verification_token(user):
        """Create a verification token with 24-hour expiry"""
        # Delete any existing tokens
        EmailVerificationToken.objects.filter(user=user).delete()
        
        # Create new token
        expires_at = timezone.now() + datetime.timedelta(hours=24)
        token = EmailVerificationToken.objects.create(
            user=user,
            expires_at=expires_at
        )
        return token
    
    @staticmethod
    def send_verification_email(user, token, request=None):
        """Send verification email with magic link"""
        base_url = settings.BASE_URL
        verification_link = f"{base_url}/verify-email/{token.token}"
        
        context = {
            'username': user.username,
            'verification_link': verification_link,
            'company_name': settings.COMPANY_NAME,
        }
        
        html_message = render_to_string('verify_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            "Verify your email address",
            plain_message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
            html_message=html_message
        )
        return True
    
    @staticmethod
    def verify_email(token_str):
        """Verify user email with token"""
        try:
            token = EmailVerificationToken.objects.get(token=token_str)
            if not token.is_valid():
                return False, "Verification link has expired"
                
            # Activate user
            user = token.user
            user.is_active = True
            user.save()
            
            # Remove token
            token.delete()
            return True, "Email verified successfully"
            
        except EmailVerificationToken.DoesNotExist:
            return False, "Invalid verification link"

class PasswordResetService:
    @staticmethod
    def create_reset_token(user):
        """Create a password reset token with 1-hour expiry"""
        # Delete any existing tokens
        PasswordResetToken.objects.filter(user=user).delete()
        
        # Create new token
        expires_at = timezone.now() + datetime.timedelta(hours=1)
        token = PasswordResetToken.objects.create(
            user=user,
            expires_at=expires_at
        )
        return token
    
    @staticmethod
    def send_reset_email(user, token):
        """Send password reset email with magic link"""
        base_url = settings.BASE_URL
        reset_link = f"{base_url}/reset-password/{token.token}"
        
        context = {
            'username': user.username,
            'reset_link': reset_link,
            'company_name': settings.COMPANY_NAME,
        }
        
        html_message = render_to_string('reset_password.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            "Reset your password",
            plain_message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
            html_message=html_message
        )
        return True
    
    @staticmethod
    def validate_token(token_str):
        """Validate if token exists and is valid"""
        try:
            token = PasswordResetToken.objects.get(token=token_str)
            if not token.is_valid():
                return None, "Reset link has expired"
            return token, None
        except PasswordResetToken.DoesNotExist:
            return None, "Invalid reset link"
        
    @staticmethod
    def reset_password(token_str, new_password):
        """Reset user password with token"""
        token, error = PasswordResetService.validate_token(token_str)
        if error:
            return False, error
            
        # Update password
        user = token.user
        user.set_password(new_password)
        user.save()
        
        # Remove token
        token.delete()
        return True, "Password reset successfully"