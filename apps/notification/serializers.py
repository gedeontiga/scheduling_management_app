from rest_framework import serializers
from apps.notification.models import Notification, ScheduledAlarm

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'type', 'title', 'message', 'is_read', 'created_at', 'actions', 'delieved']
        read_only_fields = ['id', 'created_at']
        
class ScheduledAlarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledAlarm
        fields = ['id', 'time_slot', 'minutes_before', 'scheduled_time', 'triggered']
        read_only_fields = ['id', 'scheduled_time']