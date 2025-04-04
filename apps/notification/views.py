# apps/notification/views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from apps.notification.models import Notification
from apps.notification.serializers import NotificationSerializer

class NotificationPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 50

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for notifications
    """
    serializer_class = NotificationSerializer
    # Fix: Change from class to list
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    
    def get_queryset(self):
        """Filter notifications to only show the current user's"""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read"})
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """Mark a notification as delivered (for mobile push notifications)"""
        notification = self.get_object()
        notification.delieved = True
        notification.save(update_fields=['delieved'])
        return Response(NotificationSerializer(notification).data)