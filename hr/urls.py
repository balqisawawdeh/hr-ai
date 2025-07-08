from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Main URL patterns
urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Main application URLs
    path('', views.dashboard, name='dashboard'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_add, name='employee_add'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    path('positions/', views.position_list, name='position_list'),
    path('positions/add/', views.position_add, name='position_add'),
    path('positions/<int:pk>/edit/', views.position_edit, name='position_edit'),
    path('positions/<int:pk>/delete/', views.position_delete, name='position_delete'),
    
    # Location tracking URLs
    path('location-tracking/', views.location_tracking, name='location_tracking'),
    path('geofences/', views.geofence_management, name='geofence_management'),
    path('ai-assistant/', views.ai_assistant_interface, name='ai_assistant'),
]