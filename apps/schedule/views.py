# apps/schedule/views.py
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.schedule.models import Schedule, Role, Participant, ScheduleDay, TimeSlot, PermutationRequest
from apps.schedule.serializers import (
    ScheduleSerializer, RoleSerializer, ParticipantSerializer,
    ScheduleDaySerializer, TimeSlotSerializer, PermutationRequestSerializer
)
from apps.notification.services import NotificationService

class SchedulePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Schedule operations
    """
    serializer_class = ScheduleSerializer
    # Fix: Change from class to list
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SchedulePagination
    
    def get_queryset(self):
        """
        Returns schedules where the user is either owner or participant
        """
        user = self.request.user
        return Schedule.objects.filter(
            Q(owner=user) | Q(participants__user=user)
        ).distinct()
    
    def perform_create(self, serializer):
        """
        Set the owner to the current authenticated user when creating a schedule
        """
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_participants(self, request, pk=None):
        """
        Add participants to the schedule
        """
        schedule = self.get_object()
        
        if schedule.owner != request.user:
            # Check if user has permission to invite users
            try:
                participant = Participant.objects.get(schedule=schedule, user=request.user)
                role = participant.role
                if not role.can_invate_users:
                    return Response(
                        {"detail": "You don't have permission to add participants"},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Participant.DoesNotExist:
                return Response(
                    {"detail": "You don't have permission to add participants"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Process participants
        users_data = request.data.get('participants', [])
        role_id = request.data.get('role_id')
        
        try:
            role = Role.objects.get(id=role_id, schedule=schedule)
        except Role.DoesNotExist:
            return Response(
                {"detail": "Role not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_participants = []
        errors = []
        
        for user_data in users_data:
            email = user_data.get('email')
            username = user_data.get('username')
            
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                if email:
                    user = User.objects.get(email=email)
                elif username:
                    user = User.objects.get(username=username)
                else:
                    errors.append({"detail": "Either email or username is required"})
                    continue
                
                # Check if participant already exists
                if Participant.objects.filter(schedule=schedule, user=user).exists():
                    errors.append({
                        "detail": f"User {user.username} is already a participant"
                    })
                    continue
                
                # Create participant
                participant = Participant.objects.create(
                    schedule=schedule,
                    user=user,
                    role=role
                )
                
                # Send notification to user
                NotificationService.send_schedule_invitation(
                    user, schedule, request.user, role
                )
                
                created_participants.append(ParticipantSerializer(participant).data)
                
            except User.DoesNotExist:
                errors.append({
                    "detail": f"User with {'email ' + email if email else 'username ' + username} not found"
                })
            except Exception as e:
                errors.append({"detail": str(e)})
        
        return Response({
            "created": created_participants,
            "errors": errors
        })
    
    @action(detail=True, methods=['post'])
    def mark_complete(self, request, pk=None):
        """
        Mark schedule as complete when all participants have set their availability
        """
        schedule = self.get_object()
        schedule.is_complete = True
        schedule.save(update_fields=['is_complete'])
        return Response({"detail": "Schedule marked as complete"})

class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Role operations
    """
    serializer_class = RoleSerializer
    # Fix: Change from class to list
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            return Role.objects.filter(schedule_id=schedule_id)
        return Role.objects.filter(schedule__owner=self.request.user)
    
    def perform_create(self, serializer):
        schedule_id = self.request.data.get('schedule_id')
        schedule = get_object_or_404(Schedule, id=schedule_id, owner=self.request.user)
        serializer.save(schedule=schedule)

class ScheduleDayViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ScheduleDay operations
    """
    serializer_class = ScheduleDaySerializer
    # Fix: Change from class to list
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        schedule_id = self.request.query_params.get('schedule_id')
        if schedule_id:
            return ScheduleDay.objects.filter(schedule_id=schedule_id)
        return ScheduleDay.objects.filter(
            schedule__participants__user=self.request.user
        ).distinct()

class TimeSlotViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TimeSlot operations
    """
    serializer_class = TimeSlotSerializer
    # Fix: Change from class to list
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        schedule_day_id = self.request.query_params.get('schedule_day_id')
        if schedule_day_id:
            return TimeSlot.objects.filter(schedule_day_id=schedule_day_id)
        return TimeSlot.objects.filter(
            schedule_day__schedule__participants__user=self.request.user
        ).distinct()
    
    def perform_update(self, serializer):
        """Add sync status for offline data handling"""
        serializer.save(sync_status='modified')
    
    @action(detail=True, methods=['post'])
    def set_alarm(self, request, pk=None):
        """Set alarm for a time slot"""
        time_slot = self.get_object()
        alarm_times = request.data.get('alarm_times', [])
        
        # Update time slot
        time_slot.has_alarm = bool(alarm_times)
        time_slot.alarm_times = alarm_times
        time_slot.save(update_fields=['has_alarm', 'alarm_times'])
        
        # Create scheduled alarms for the user
        from apps.notification.models import ScheduledAlarm
        from datetime import datetime, timedelta
        
        # Get the date from the schedule day
        date = time_slot.schedule_day.date
        
        # Delete existing alarms for this time slot and user
        ScheduledAlarm.objects.filter(
            time_slot=time_slot,
            user=request.user
        ).delete()
        
        # Create new alarms
        created_alarms = []
        for minutes in alarm_times:
            # Calculate scheduled time by combining date and time, then subtracting minutes
            start_datetime = datetime.combine(date, time_slot.start_time)
            scheduled_time = start_datetime - timedelta(minutes=minutes)
            
            alarm = ScheduledAlarm.objects.create(
                user=request.user,
                time_slot=time_slot,
                minutes_before=minutes,
                scheduled_time=scheduled_time
            )
            created_alarms.append(alarm.id)
        
        return Response({
            "has_alarm": time_slot.has_alarm,
            "alarm_times": time_slot.alarm_times,
            "created_alarms": created_alarms
        })

class PermutationRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for handling permutation requests
    """
    serializer_class = PermutationRequestSerializer
    # Fix: Change from class to list
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return PermutationRequest.objects.filter(
            Q(requester__user=user) | Q(recipient__user=user)
        )
    
    def create(self, request, *args, **kwargs):
        requester_slot_id = request.data.get('requester_slot_id')
        recipient_slot_id = request.data.get('recipient_slot_id')
        message = request.data.get('message', '')
        
        # Get time slots
        requester_slot = get_object_or_404(TimeSlot, id=requester_slot_id)
        recipient_slot = get_object_or_404(TimeSlot, id=recipient_slot_id)
        
        # Get participants
        try:
            requester = Participant.objects.get(
                schedule=requester_slot.schedule_day.schedule,
                user=request.user
            )
            
            # Find recipient based on the participants in the recipient slot
            recipient = recipient_slot.participants.first()
            
            if not recipient:
                return Response(
                    {"detail": "Recipient time slot has no assigned participants"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Check if requester role allows permutation requests
            if not requester.role.can_request_permutations:
                return Response(
                    {"detail": "Your role does not allow permutation requests"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Create permutation request
            permutation = PermutationRequest.objects.create(
                requester=requester,
                recipient=recipient,
                requester_slot=requester_slot,
                recipient_slot=recipient_slot,
                message=message,
                status='Pending'
            )
            
            # Send notification to recipient
            NotificationService.send_permutation_request(
                recipient.user, permutation
            )
            
            return Response(
                PermutationRequestSerializer(permutation).data,
                status=status.HTTP_201_CREATED
            )
            
        except Participant.DoesNotExist:
            return Response(
                {"detail": "You must be a participant in this schedule"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a permutation request"""
        permutation = self.get_object()
        
        # Verify that the current user is the recipient
        if permutation.recipient.user != request.user:
            return Response(
                {"detail": "Only the recipient can accept the permutation"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update status
        permutation.status = 'Accepted'
        permutation.save(update_fields=['status'])
        
        # Swap participants in time slots
        requester_participants = list(permutation.requester_slot.participants.all())
        recipient_participants = list(permutation.recipient_slot.participants.all())
        
        # Clear participants
        permutation.requester_slot.participants.clear()
        permutation.recipient_slot.participants.clear()
        
        # Swap participants
        for participant in requester_participants:
            permutation.recipient_slot.participants.add(participant)
        
        for participant in recipient_participants:
            permutation.requester_slot.participants.add(participant)
        
        # Send notification to requester
        NotificationService.send_permutation_response(
            permutation.requester.user, permutation, accepted=True
        )
        
        return Response({
            "detail": "Permutation accepted successfully",
            "permutation": PermutationRequestSerializer(permutation).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a permutation request"""
        permutation = self.get_object()
        
        # Verify that the current user is the recipient
        if permutation.recipient.user != request.user:
            return Response(
                {"detail": "Only the recipient can reject the permutation"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update status
        permutation.status = 'Rejected'
        permutation.save(update_fields=['status'])
        
        # Send notification to requester
        NotificationService.send_permutation_response(
            permutation.requester.user, permutation, accepted=False
        )
        
        return Response({
            "detail": "Permutation rejected successfully",
            "permutation": PermutationRequestSerializer(permutation).data
        })