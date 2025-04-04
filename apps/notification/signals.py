
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

from apps.notification.models import Notification
from apps.notification.serializers import NotificationSerializer
from apps.schedule.models import PermutationRequest
from apps.schedule.serializers import PermutationRequestSerializer

@receiver(post_save, sender=Notification)
def notification_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a notification is created.
    Sends the notification to the user via WebSocket.
    """
    if created:
        channel_layer = get_channel_layer()
        user_id = str(instance.user.id)
        
        # Serialize notification
        serializer = NotificationSerializer(instance)
        
        # Send to user's notification group
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user_id}",
            {
                "type": "notification_message",
                "notification": serializer.data
            }
        )

@receiver(post_save, sender=PermutationRequest)
def permutation_updated(sender, instance, **kwargs):
    """
    Signal handler for when a permutation request is updated.
    Sends the update to both requester and recipient via WebSocket.
    """
    channel_layer = get_channel_layer()
    
    # Serialize permutation
    serializer = PermutationRequestSerializer(instance)
    
    # Send to requester
    requester_id = str(instance.requester.user.id)
    async_to_sync(channel_layer.group_send)(
        f"notifications_{requester_id}",
        {
            "type": "permutation_update",
            "permutation": serializer.data
        }
    )
    
    # Send to recipient
    recipient_id = str(instance.recipient.user.id)
    async_to_sync(channel_layer.group_send)(
        f"notifications_{recipient_id}",
        {
            "type": "permutation_update",
            "permutation": serializer.data
        }
    )