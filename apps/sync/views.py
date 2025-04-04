# apps/schedule/sync_views.py
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.utils import timezone

from apps.schedule.models import Schedule, TimeSlot
from apps.schedule.serializers import TimeSlotSerializer
from apps.users.services import SyncService

class SyncTimeSlotView(views.APIView):
    """
    API endpoint for synchronizing time slots between client and server
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Handle client-to-server sync of time slots
        
        Expected payload:
        {
            "time_slots": [
                {
                    "id": "uuid",
                    "is_available": true,
                    "has_alarm": false,
                    "alarm_times": [],
                    "last_modified": "2024-03-31T12:34:56.789Z",
                    "sync_status": "modified"
                },
                ...
            ]
        }
        """
        time_slots_data = request.data.get('time_slots', [])
        
        if not time_slots_data:
            return Response(
                {"detail": "No time slots provided for synchronization"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process sync
        sync_results = SyncService.sync_time_slots(request.user, time_slots_data)
        
        # Update user's last synced timestamp
        request.user.last_synced_at = timezone.now()
        request.user.save(update_fields=['last_synced_at'])
        
        # Return sync results
        return Response({
            "updated_count": len(sync_results['updated']),
            "error_count": len(sync_results['errors']),
            "updated": sync_results['updated'],
            "errors": sync_results['errors'],
            "last_synced_at": request.user.last_synced_at
        })
    
    def get(self, request):
        """
        Get all time slots that need to be synchronized to the client
        
        This endpoint returns all time slots that have been modified since
        the user's last sync time.
        """
        last_synced_at = request.user.last_synced_at
        
        if not last_synced_at:
            # If this is the first sync, return all time slots
            schedules = Schedule.objects.filter(participants__user=request.user)
            time_slots = TimeSlot.objects.filter(schedule_day__schedule__in=schedules)
        else:
            # Otherwise, return only time slots modified since last sync
            schedules = Schedule.objects.filter(participants__user=request.user)
            time_slots = TimeSlot.objects.filter(
                schedule_day__schedule__in=schedules,
                last_modified__gt=last_synced_at
            )
        
        serializer = TimeSlotSerializer(time_slots, many=True)
        
        return Response({
            "time_slots": serializer.data,
            "count": time_slots.count(),
            "last_synced_at": request.user.last_synced_at
        })