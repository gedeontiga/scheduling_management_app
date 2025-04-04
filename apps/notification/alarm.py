
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from apps.notification.models import ScheduledAlarm
from apps.notification.services import NotificationService

class Command(BaseCommand):
    help = 'Trigger scheduled alarms that are due'
    
    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find all scheduled alarms that are:
        # 1. Not yet triggered
        # 2. Scheduled time is in the past or now
        due_alarms = ScheduledAlarm.objects.filter(
            triggered=False, 
            scheduled_time__lte=now
        )
        
        self.stdout.write(f"Found {due_alarms.count()} alarms to trigger")
        
        triggered_count = 0
        for alarm in due_alarms:
            try:
                # Create notification for the alarm
                notification = NotificationService.send_alarm_notification(alarm)
                
                # Mark the alarm as triggered
                alarm.triggered = True
                alarm.save(update_fields=['triggered'])
                
                self.stdout.write(f"Triggered alarm for user {alarm.user.username} at {alarm.scheduled_time}")
                triggered_count += 1
                
            except Exception as e:
                self.stderr.write(f"Error triggering alarm {alarm.id}: {str(e)}")
                
        self.stdout.write(self.style.SUCCESS(f"Successfully triggered {triggered_count} alarms"))

# The command can be run as a cron job every minute:
# * * * * * python manage.py trigger_alarms