from django.apps import AppConfig


class NotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notification'
    
    def ready(self):
        # Import signals
        import apps.notification.signals
