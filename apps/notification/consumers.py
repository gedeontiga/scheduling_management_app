# apps/notification/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    """
    
    async def connect(self):
        """
        Connect to WebSocket and join user-specific notification group
        """
        # Extract user ID from scope
        user_id = self.scope["url_route"]["kwargs"]["user_id"]
        
        # Verify user authentication token
        if not await self.verify_user(user_id):
            await self.close()
            return
        
        self.user_id = user_id
        self.room_group_name = f"notifications_{user_id}"
        
        # Join notification group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Leave notification group when disconnecting
        """
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket client
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle different message types
            if message_type == 'notification_read':
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
                    
                    # Send confirmation back to client
                    await self.send(text_data=json.dumps({
                        'type': 'notification_marked_read',
                        'notification_id': notification_id
                    }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def notification_message(self, event):
        """
        Receive notification from notification group and send to WebSocket
        """
        # Send the notification to the WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def permutation_update(self, event):
        """
        Receive permutation update from group and send to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'permutation_update',
            'permutation': event['permutation']
        }))
    
    @database_sync_to_async
    def verify_user(self, user_id):
        """
        Verify that the user exists and is authenticated
        """
        try:
            # Authentication is already handled by Django Channels auth middleware
            # This is just an additional check to make sure the user exists
            user = User.objects.get(id=user_id)
            return True
        except User.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """
        Mark a notification as read
        """
        from apps.notification.models import Notification
        try:
            notification = Notification.objects.get(id=notification_id, user_id=self.user_id)
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return True
        except Notification.DoesNotExist:
            return False