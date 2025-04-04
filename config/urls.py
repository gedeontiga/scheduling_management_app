# config/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.users.views import AuthViewSet, UserViewSet
from apps.schedule.views import (
    ScheduleViewSet, RoleViewSet, ScheduleDayViewSet, 
    TimeSlotViewSet, PermutationRequestViewSet
)
from apps.notification.views import NotificationViewSet
from apps.export.views import ExportScheduleView

# Create a router for our viewsets
router = DefaultRouter()

# Users app endpoints
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='users')

# Schedule app endpoints
router.register(r'schedules', ScheduleViewSet, basename='schedules')
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'schedule-days', ScheduleDayViewSet, basename='schedule-days')
router.register(r'time-slots', TimeSlotViewSet, basename='time-slots')
router.register(r'permutation-requests', PermutationRequestViewSet, basename='permutation-requests')

# Notification app endpoints
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Export endpoint
    path('api/export/schedule/<uuid:schedule_id>/', ExportScheduleView.as_view(), name='export-schedule'),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]