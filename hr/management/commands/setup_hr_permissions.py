from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from hr.models import Employee, Department, Position, EmployeeDocument, EmployeeNote


class Command(BaseCommand):
    help = 'Set up HR groups and permissions'

    def handle(self, *args, **options):
        # Create HR Personnel group
        hr_personnel_group, created = Group.objects.get_or_create(name='HR Personnel')
        if created:
            self.stdout.write(self.style.SUCCESS('Created HR Personnel group'))
        
        # Create HR Managers group
        hr_managers_group, created = Group.objects.get_or_create(name='HR Managers')
        if created:
            self.stdout.write(self.style.SUCCESS('Created HR Managers group'))
        
        # Get content types
        employee_ct = ContentType.objects.get_for_model(Employee)
        department_ct = ContentType.objects.get_for_model(Department)
        position_ct = ContentType.objects.get_for_model(Position)
        document_ct = ContentType.objects.get_for_model(EmployeeDocument)
        note_ct = ContentType.objects.get_for_model(EmployeeNote)
        
        # HR Personnel permissions (view only)
        hr_personnel_permissions = [
            Permission.objects.get(codename='view_employee', content_type=employee_ct),
            Permission.objects.get(codename='view_department', content_type=department_ct),
            Permission.objects.get(codename='view_position', content_type=position_ct),
            Permission.objects.get(codename='view_employeedocument', content_type=document_ct),
            Permission.objects.get(codename='view_employeenote', content_type=note_ct),
        ]
        
        # HR Managers permissions (full CRUD)
        hr_managers_permissions = [
            # Employee permissions
            Permission.objects.get(codename='add_employee', content_type=employee_ct),
            Permission.objects.get(codename='change_employee', content_type=employee_ct),
            Permission.objects.get(codename='delete_employee', content_type=employee_ct),
            Permission.objects.get(codename='view_employee', content_type=employee_ct),
            
            # Department permissions
            Permission.objects.get(codename='add_department', content_type=department_ct),
            Permission.objects.get(codename='change_department', content_type=department_ct),
            Permission.objects.get(codename='delete_department', content_type=department_ct),
            Permission.objects.get(codename='view_department', content_type=department_ct),
            
            # Position permissions
            Permission.objects.get(codename='add_position', content_type=position_ct),
            Permission.objects.get(codename='change_position', content_type=position_ct),
            Permission.objects.get(codename='delete_position', content_type=position_ct),
            Permission.objects.get(codename='view_position', content_type=position_ct),
            
            # Document permissions
            Permission.objects.get(codename='add_employeedocument', content_type=document_ct),
            Permission.objects.get(codename='change_employeedocument', content_type=document_ct),
            Permission.objects.get(codename='delete_employeedocument', content_type=document_ct),
            Permission.objects.get(codename='view_employeedocument', content_type=document_ct),
            
            # Note permissions
            Permission.objects.get(codename='add_employeenote', content_type=note_ct),
            Permission.objects.get(codename='change_employeenote', content_type=note_ct),
            Permission.objects.get(codename='delete_employeenote', content_type=note_ct),
            Permission.objects.get(codename='view_employeenote', content_type=note_ct),
        ]
        
        # Assign permissions to groups
        hr_personnel_group.permissions.set(hr_personnel_permissions)
        hr_managers_group.permissions.set(hr_managers_permissions)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully set up HR groups and permissions:\n'
                f'- HR Personnel: {len(hr_personnel_permissions)} permissions\n'
                f'- HR Managers: {len(hr_managers_permissions)} permissions'
            )
        )

