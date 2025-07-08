from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test

from .models import Employee, Department, Position, CheckInLocation, EmployeeStatus, Geofence, LocationHistory
from .forms import (
    EmployeeForm, DepartmentForm, PositionForm, GeofenceForm,
    EmployeeDocumentForm, EmployeeNoteForm
)
from .auth_views import hr_required, hr_manager_required


@hr_required
def dashboard(request):
    """Main dashboard view"""
    today = timezone.now().date()
    
    # Get basic statistics
    total_employees = Employee.objects.count()
    total_departments = Department.objects.count()
    total_positions = Position.objects.count()
    
    # Get today's check-ins if location tracking is available
    todays_checkins = 0
    try:
        todays_checkins = CheckInLocation.objects.filter(
            timestamp__date=today,
            check_type='in'
        ).count()
    except:
        pass
    
    # Get recent employees
    recent_employees = Employee.objects.order_by('-created_at')[:5]
    
    context = {
        'total_employees': total_employees,
        'total_departments': total_departments,
        'total_positions': total_positions,
        'todays_checkins': todays_checkins,
        'recent_employees': recent_employees,
    }
    
    return render(request, 'hr/dashboard.html', context)


@hr_required
def employee_list(request):
    """List all employees with search and filter functionality"""
    form = EmployeeSearchForm(request.GET)
    employees = Employee.objects.select_related('department', 'position', 'manager').all()
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        department = form.cleaned_data.get('department')
        position = form.cleaned_data.get('position')
        employment_status = form.cleaned_data.get('employment_status')
        
        if search_query:
            employees = employees.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )
        
        if department:
            employees = employees.filter(department=department)
        
        if position:
            employees = employees.filter(position=position)
        
        if employment_status:
            employees = employees.filter(employment_status=employment_status)
    
    # Pagination
    paginator = Paginator(employees, 20)  # Show 20 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'employees': page_obj,
        'total_count': employees.count(),
    }
    
    return render(request, 'hr/employee_list.html', context)


@hr_required
def employee_detail(request, employee_id):
    """Display detailed information about an employee"""
    employee = get_object_or_404(Employee, pk=employee_id)
    documents = employee.documents.all()[:5]  # Show latest 5 documents
    notes = employee.notes.all()[:5]  # Show latest 5 notes
    
    context = {
        'employee': employee,
        'documents': documents,
        'notes': notes,
        'can_edit': request.user.has_perm('hr.change_employee'),
    }
    
    return render(request, 'hr/employee_detail.html', context)


@hr_manager_required
def employee_add(request):
    """Add a new employee"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.created_by = request.user
            employee.save()
            messages.success(request, f'Employee {employee.full_name} has been added successfully.')
            return redirect('employee_detail', employee_id=employee.pk)
    else:
        form = EmployeeForm()
    
    context = {
        'form': form,
        'title': 'Add New Employee',
        'submit_text': 'Add Employee',
    }
    
    return render(request, 'hr/employee_form.html', context)


@hr_manager_required
def employee_edit(request, employee_id):
    """Edit an existing employee"""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee {employee.full_name} has been updated successfully.')
            return redirect('employee_detail', employee_id=employee.pk)
    else:
        form = EmployeeForm(instance=employee)
    
    context = {
        'form': form,
        'employee': employee,
        'title': f'Edit {employee.full_name}',
        'submit_text': 'Update Employee',
    }
    
    return render(request, 'hr/employee_form.html', context)


@hr_required
def department_list(request):
    """List all departments"""
    departments = Department.objects.select_related('manager').all()
    
    context = {
        'departments': departments,
        'can_add': request.user.has_perm('hr.add_department'),
    }
    
    return render(request, 'hr/department_list.html', context)


@hr_manager_required
def department_add(request):
    """Add a new department"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department {department.name} has been added successfully.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    
    context = {
        'form': form,
        'title': 'Add New Department',
        'submit_text': 'Add Department',
    }
    
    return render(request, 'hr/department_form.html', context)


@hr_required
def position_list(request):
    """List all positions"""
    positions = Position.objects.all()
    
    context = {
        'positions': positions,
        'can_add': request.user.has_perm('hr.add_position'),
    }
    
    return render(request, 'hr/position_list.html', context)


@hr_manager_required
def position_add(request):
    """Add a new position"""
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            position = form.save()
            messages.success(request, f'Position {position.title} has been added successfully.')
            return redirect('position_list')
    else:
        form = PositionForm()
    
    context = {
        'form': form,
        'title': 'Add New Position',
        'submit_text': 'Add Position',
    }
    
    return render(request, 'hr/position_form.html', context)


@hr_manager_required
def employee_document_add(request, employee_id):
    """Add a document for an employee"""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.uploaded_by = request.user
            document.save()
            messages.success(request, 'Document has been uploaded successfully.')
            return redirect('employee_detail', employee_id=employee.pk)
    else:
        form = EmployeeDocumentForm()
    
    context = {
        'form': form,
        'employee': employee,
        'title': f'Add Document for {employee.full_name}',
        'submit_text': 'Upload Document',
    }
    
    return render(request, 'hr/document_form.html', context)


@hr_manager_required
def employee_note_add(request, employee_id):
    """Add a note for an employee"""
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if request.method == 'POST':
        form = EmployeeNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.employee = employee
            note.created_by = request.user
            note.save()
            messages.success(request, 'Note has been added successfully.')
            return redirect('employee_detail', employee_id=employee.pk)
    else:
        form = EmployeeNoteForm()
    
    context = {
        'form': form,
        'employee': employee,
        'title': f'Add Note for {employee.full_name}',
        'submit_text': 'Add Note',
    }
    
    return render(request, 'hr/note_form.html', context)


@hr_required
@require_http_methods(["GET"])
def employee_search_api(request):
    """API endpoint for employee search (for AJAX requests)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'employees': []})
    
    employees = Employee.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(employee_id__icontains=query)
    ).filter(employment_status='active')[:10]
    
    employee_data = [
        {
            'id': emp.pk,
            'name': emp.full_name,
            'employee_id': emp.employee_id,
            'department': emp.department.name,
            'position': emp.position.title,
        }
        for emp in employees
    ]
    
    return JsonResponse({'employees': employee_data})


from django.utils import timezone
from .models import CheckInLocation, EmployeeStatus, Geofence, LocationHistory


@login_required
def location_tracking(request):
    """Location tracking dashboard"""
    today = timezone.now().date()
    
    # Get today's check-ins
    todays_checkins = CheckInLocation.objects.filter(
        timestamp__date=today,
        check_type='in'
    ).select_related('employee').order_by('-timestamp')
    
    # Get current employee statuses
    employee_statuses = EmployeeStatus.objects.select_related(
        'employee', 'current_geofence'
    ).order_by('employee__full_name')
    
    # Get active geofences
    geofences = Geofence.objects.filter(is_active=True)
    
    context = {
        'todays_checkins': todays_checkins,
        'employee_statuses': employee_statuses,
        'geofences': geofences,
        'total_employees': Employee.objects.count(),
        'checked_in_today': todays_checkins.count(),
    }
    
    return render(request, 'hr/location_tracking.html', context)


@login_required
def geofence_management(request):
    """Geofence management interface"""
    geofences = Geofence.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = GeofenceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Geofence created successfully!')
            return redirect('geofence_management')
    else:
        form = GeofenceForm()
    
    context = {
        'geofences': geofences,
        'form': form,
    }
    
    return render(request, 'hr/geofence_management.html', context)


@login_required
def ai_assistant_interface(request):
    """AI assistant interface"""
    context = {
        'page_title': 'AI Assistant',
    }
    
    return render(request, 'hr/ai_assistant.html', context)



@hr_manager_required
def employee_delete(request, pk):
    """Delete an employee"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee.delete()
        messages.success(request, f'Employee {employee.full_name} deleted successfully!')
        return redirect('employee_list')
    
    context = {'employee': employee}
    return render(request, 'hr/employee_confirm_delete.html', context)


@hr_manager_required
def employee_edit(request, pk):
    """Edit an employee"""
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, f'Employee {employee.full_name} updated successfully!')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    
    context = {
        'form': form,
        'employee': employee,
        'page_title': f'Edit {employee.full_name}'
    }
    return render(request, 'hr/employee_form.html', context)


@hr_manager_required
def department_edit(request, pk):
    """Edit a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f'Department {department.name} updated successfully!')
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    
    context = {
        'form': form,
        'department': department,
        'page_title': f'Edit {department.name}'
    }
    return render(request, 'hr/department_form.html', context)


@hr_manager_required
def department_delete(request, pk):
    """Delete a department"""
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        department.delete()
        messages.success(request, f'Department {department.name} deleted successfully!')
        return redirect('department_list')
    
    context = {'department': department}
    return render(request, 'hr/department_confirm_delete.html', context)


@hr_manager_required
def position_edit(request, pk):
    """Edit a position"""
    position = get_object_or_404(Position, pk=pk)
    
    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            messages.success(request, f'Position {position.title} updated successfully!')
            return redirect('position_list')
    else:
        form = PositionForm(instance=position)
    
    context = {
        'form': form,
        'position': position,
        'page_title': f'Edit {position.title}'
    }
    return render(request, 'hr/position_form.html', context)


@hr_manager_required
def position_delete(request, pk):
    """Delete a position"""
    position = get_object_or_404(Position, pk=pk)
    
    if request.method == 'POST':
        position.delete()
        messages.success(request, f'Position {position.title} deleted successfully!')
        return redirect('position_list')
    
    context = {'position': position}
    return render(request, 'hr/position_confirm_delete.html', context)

