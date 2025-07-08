from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from functools import wraps


def hr_required(view_func):
    """
    Decorator to ensure only HR personnel can access certain views
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user has HR permissions or is staff
        if (request.user.is_staff or 
            request.user.has_perm('hr.view_employee') or
            request.user.groups.filter(name='HR Personnel').exists()):
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("You don't have permission to access this page.")
    
    return _wrapped_view


def hr_manager_required(view_func):
    """
    Decorator to ensure only HR managers can access certain views
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user has HR manager permissions
        if (request.user.is_staff or 
            request.user.has_perm('hr.add_employee') or
            request.user.groups.filter(name='HR Managers').exists()):
            return view_func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden("You don't have permission to access this page.")
    
    return _wrapped_view


def login_view(request):
    """
    Custom login view for HR personnel
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Check if user has HR permissions
                if (user.is_staff or 
                    user.has_perm('hr.view_employee') or
                    user.groups.filter(name__in=['HR Personnel', 'HR Managers']).exists()):
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    next_url = request.GET.get('next', 'dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'You do not have permission to access the HR system.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'registration/login.html')


def logout_view(request):
    """
    Custom logout view
    """
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


@hr_required
def dashboard(request):
    """
    Main dashboard for HR personnel
    """
    from .models import Employee, Department, Position
    
    context = {
        'total_employees': Employee.objects.filter(employment_status='active').count(),
        'total_departments': Department.objects.count(),
        'total_positions': Position.objects.count(),
        'recent_hires': Employee.objects.filter(employment_status='active').order_by('-hire_date')[:5],
        'user': request.user,
    }
    
    return render(request, 'hr/dashboard.html', context)

