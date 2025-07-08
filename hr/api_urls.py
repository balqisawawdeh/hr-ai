from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

# Create router for viewsets
router = DefaultRouter()
router.register(r'checkins', api_views.CheckInLocationViewSet)
router.register(r'employee-status', api_views.EmployeeStatusViewSet)
router.register(r'geofences', api_views.GeofenceViewSet)

# API URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('check-in/', api_views.check_in, name='api_check_in'),
    path('check-out/', api_views.check_out, name='api_check_out'),
    path('update-location/', api_views.update_location, name='api_update_location'),
    path('ai-assistant/query/', api_views.ai_assistant_query, name='api_ai_query'),
    path('employees/<int:employee_id>/location/', api_views.employee_current_location, name='api_employee_location'),
    path('analytics/', api_views.location_analytics, name='api_location_analytics'),
]

