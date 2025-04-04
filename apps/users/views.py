# apps/users/views.py
import uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.serializers import UserSerializer, UserRegistrationSerializer
from apps.users.services import EmailVerificationService, PasswordResetService

User = get_user_model()

class AuthViewSet(viewsets.GenericViewSet):
    """
    API endpoint for user authentication operations
    """
    # Fix: Add default serializer_class to resolve the error
    serializer_class = UserRegistrationSerializer
    # Fix: Change from class to list to make it iterable
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Create inactive user
            user = serializer.save(is_active=False)
            
            # Create and send verification token
            token = EmailVerificationService.create_verification_token(user)
            EmailVerificationService.send_verification_email(user, token, request)
            
            return Response({
                'detail': 'User registered successfully. Please check your email to verify your account.',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def verify_email(self, request):
        token = request.query_params.get('token')
        if not token:
            return Response({'detail': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        success, message = EmailVerificationService.verify_email(token)
        if success:
            return Response({'detail': message}, status=status.HTTP_200_OK)
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_token(self, request):
        """Verify if token is valid"""
        # Token validation is automatically done by JWT middleware
        return Response({"detail": "Token is valid"}, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['post'])
    def update_device_token(self, request):
        """Update device token for push notifications"""
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, 
                            status=status.HTTP_401_UNAUTHORIZED)
            
        device_token = request.data.get('device_token')
        if not device_token:
            return Response({"detail": "Device token is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        tokens = user.device_tokens or []
        
        if device_token not in tokens:
            tokens.append(device_token)
            user.device_tokens = tokens
            user.save(update_fields=['device_tokens'])
            
        return Response({"detail": "Device token updated successfully"}, 
                        status=status.HTTP_200_OK)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user information
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # Fix: Change from class to list to make it iterable
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user info"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update user profile"""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['put'])
    def update_sync_time(self, request):
        """Update last synced timestamp"""
        user = request.user
        user.last_synced_at = timezone.now()
        user.save(update_fields=['last_synced_at'])
        
        return Response({
            "last_synced_at": user.last_synced_at
        })
            
    @action(detail=False, methods=['post'])
    def forgot_password(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(email=email)
            token = PasswordResetService.create_reset_token(user)
            PasswordResetService.send_reset_email(user, token)
            return Response({'detail': 'Password reset instructions sent to your email'})
        except User.DoesNotExist:
            # Return success even if user doesn't exist for security
            return Response({'detail': 'Password reset instructions sent to your email'})

    @action(detail=False, methods=['post'])
    def reset_password(self, request):
        token = request.data.get('token')
        password = request.data.get('password')
        
        if not token or not password:
            return Response({
                'detail': 'Token and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success, message = PasswordResetService.reset_password(token, password)
        if success:
            return Response({'detail': message})
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)