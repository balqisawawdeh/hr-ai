from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Department, Position, Employee, EmployeeDocument, EmployeeNote,
    CheckInLocation, Geofence, LocationHistory, EmployeeStatus
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'employee_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Employee Count'


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'salary_range', 'employee_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'description']
    ordering = ['title']

    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"${obj.salary_min:,.2f} - ${obj.salary_max:,.2f}"
        return "Not specified"
    salary_range.short_description = 'Salary Range'

    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = 'Employee Count'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 'full_name', 'email', 'department', 
        'position', 'employment_status', 'hire_date'
    ]
    list_filter = [
        'employment_status', 'employment_type', 'department', 
        'position', 'hire_date'
    ]
    search_fields = [
        'employee_id', 'first_name', 'last_name', 'email', 
        'phone_number'
    ]
    ordering = ['last_name', 'first_name']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'employee_id', 'first_name', 'last_name', 'email', 
                'phone_number', 'date_of_birth'
            )
        }),
        ('Address', {
            'fields': (
                'address_line1', 'address_line2', 'city', 'state', 
                'postal_code', 'country'
            )
        }),
        ('Employment Information', {
            'fields': (
                'department', 'position', 'employment_status', 
                'employment_type', 'hire_date', 'termination_date', 
                'salary', 'manager'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone', 
                'emergency_contact_relationship'
            )
        }),
        ('System Information', {
            'fields': ('user', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'
    full_name.admin_order_field = 'last_name'


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'title', 'document_type', 'uploaded_at', 'uploaded_by']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'title']
    ordering = ['-uploaded_at']


@admin.register(EmployeeNote)
class EmployeeNoteAdmin(admin.ModelAdmin):
    list_display = ['employee', 'title', 'is_confidential', 'created_at', 'created_by']
    list_filter = ['is_confidential', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'title', 'content']
    ordering = ['-created_at']



@admin.register(CheckInLocation)
class CheckInLocationAdmin(admin.ModelAdmin):
    list_display = ['employee', 'check_type', 'timestamp', 'is_within_geofence', 'location_string']
    list_filter = ['check_type', 'is_within_geofence', 'timestamp']
    search_fields = ['employee__full_name', 'employee__employee_id']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def location_string(self, obj):
        return f"{obj.latitude}, {obj.longitude}"
    location_string.short_description = 'Location'


@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'center_latitude', 'center_longitude', 'radius', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LocationHistory)
class LocationHistoryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'timestamp', 'latitude', 'longitude', 'accuracy']
    list_filter = ['timestamp']
    search_fields = ['employee__full_name', 'employee__employee_id']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']


@admin.register(EmployeeStatus)
class EmployeeStatusAdmin(admin.ModelAdmin):
    list_display = ['employee', 'status', 'current_geofence', 'last_update', 'is_online']
    list_filter = ['status', 'current_geofence']
    search_fields = ['employee__full_name', 'employee__employee_id']
    readonly_fields = ['last_update']
    
    def is_online(self, obj):
        return obj.is_online
    is_online.boolean = True
    is_online.short_description = 'Online'

