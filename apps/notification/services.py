# apps/notification/services.py
from apps.notification.models import Notification, NotificationTypes

class NotificationService:
    """
    Service for handling notification creation and delivery
    """
    
    @staticmethod
    def send_schedule_invitation(user, schedule, inviter, role):
        """
        Send a schedule invitation notification
        """
        title = f"Invitation to join {schedule.name}"
        message = f"{inviter.username} has invited you to join the schedule '{schedule.name}' as {role.name}"
        
        # Create actions for easy handling in the frontend
        actions = {
            "accept": {
                "label": "Accept",
                "schedule_id": str(schedule.id)
            },
            "decline": {
                "label": "Decline",
                "schedule_id": str(schedule.id)
            }
        }
        
        return Notification.objects.create(
            user=user,
            type=NotificationTypes.SCHEDULE_INVITATION,
            title=title,
            message=message,
            actions=actions
        )
    
    @staticmethod
    def send_permutation_request(user, permutation_request):
        """
        Send a permutation request notification
        """
        requester = permutation_request.requester.user
        schedule = permutation_request.requester_slot.schedule_day.schedule
        
        title = f"Permutation Request from {requester.username}"
        
        # Format the date and time slots for better readability
        requester_day = permutation_request.requester_slot.schedule_day.date
        requester_time = f"{permutation_request.requester_slot.start_time.strftime('%H:%M')} - {permutation_request.requester_slot.end_time.strftime('%H:%M')}"
        
        recipient_day = permutation_request.recipient_slot.schedule_day.date
        recipient_time = f"{permutation_request.recipient_slot.start_time.strftime('%H:%M')} - {permutation_request.recipient_slot.end_time.strftime('%H:%M')}"
        
        message = (
            f"{requester.username} requested to switch:\n"
            f"Their slot: {requester_day} {requester_time}\n"
            f"Your slot: {recipient_day} {recipient_time}"
        )
        
        if permutation_request.message:
            message += f"\n\nMessage: {permutation_request.message}"
        
        # Create actions for easy handling in the frontend
        actions = {
            "accept": {
                "label": "Accept",
                "permutation_id": str(permutation_request.id)
            },
            "reject": {
                "label": "Reject",
                "permutation_id": str(permutation_request.id)
            },
            "view_schedule": {
                "label": "View Schedule",
                "schedule_id": str(schedule.id)
            }
        }
        
        return Notification.objects.create(
            user=user,
            type=NotificationTypes.PERMUTATION_REQUEST,
            title=title,
            message=message,
            actions=actions
        )
    
    @staticmethod
    def send_permutation_response(user, permutation_request, accepted=True):
        """
        Send a permutation response notification
        """
        recipient = permutation_request.recipient.user
        schedule = permutation_request.requester_slot.schedule_day.schedule
        
        status = "accepted" if accepted else "rejected"
        title = f"Permutation {status.capitalize()} by {recipient.username}"
        
        # Format the date and time slots for better readability
        requester_day = permutation_request.requester_slot.schedule_day.date
        requester_time = f"{permutation_request.requester_slot.start_time.strftime('%H:%M')} - {permutation_request.requester_slot.end_time.strftime('%H:%M')}"
        
        recipient_day = permutation_request.recipient_slot.schedule_day.date
        recipient_time = f"{permutation_request.recipient_slot.start_time.strftime('%H:%M')} - {permutation_request.recipient_slot.end_time.strftime('%H:%M')}"
        
        message = (
            f"{recipient.username} has {status} your permutation request to switch:\n"
            f"Your slot: {requester_day} {requester_time}\n"
            f"Their slot: {recipient_day} {recipient_time}"
        )
        
        # Create actions for easy handling in the frontend
        actions = {
            "view_schedule": {
                "label": "View Schedule",
                "schedule_id": str(schedule.id)
            }
        }
        
        return Notification.objects.create(
            user=user,
            type=NotificationTypes.PERMUTATION_RESPONSE,
            title=title,
            message=message,
            actions=actions
        )
    
    @staticmethod
    def send_alarm_notification(scheduled_alarm):
        """
        Send an alarm notification for a time slot
        """
        user = scheduled_alarm.user
        time_slot = scheduled_alarm.time_slot
        schedule_day = time_slot.schedule_day
        schedule = schedule_day.schedule
        
        title = f"Reminder: Upcoming Schedule at {time_slot.start_time.strftime('%H:%M')}"
        message = (
            f"You have a scheduled time slot in {schedule.name} "
            f"on {schedule_day.date} at {time_slot.start_time.strftime('%H:%M')} "
            f"to {time_slot.end_time.strftime('%H:%M')}"
        )
        
        # Create actions for easy handling in the frontend
        actions = {
            "view_schedule": {
                "label": "View Schedule",
                "schedule_id": str(schedule.id)
            }
        }
        
        notification = Notification.objects.create(
            user=user,
            type=NotificationTypes.ALARM,
            title=title,
            message=message,
            actions=actions
        )
        
        # Mark the alarm as triggered
        scheduled_alarm.triggered = True
        scheduled_alarm.save(update_fields=['triggered'])
        
        return notification