from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Employee, Department, Position, EmployeeDocument, EmployeeNote, Geofence


class EmployeeForm(forms.ModelForm):
    """Form for creating and editing employees"""
    
    class Meta:
        model = Employee
        fields = [
            'employee_id', 'first_name', 'last_name', 'email', 'phone_number',
            'date_of_birth', 'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'department', 'position', 'employment_status',
            'employment_type', 'hire_date', 'termination_date', 'salary', 'manager',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'termination_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., EMP001'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.Select(attrs={'class': 'form-control'}),
            'employment_status': forms.Select(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter manager choices to exclude the current employee
        if self.instance.pk:
            self.fields['manager'].queryset = Employee.objects.filter(
                employment_status='active'
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['manager'].queryset = Employee.objects.filter(
                employment_status='active'
            )

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if not employee_id.isalnum() or not employee_id.isupper():
            raise ValidationError('Employee ID must contain only uppercase letters and numbers.')
        return employee_id

    def clean_hire_date(self):
        hire_date = self.cleaned_data['hire_date']
        if hire_date > timezone.now().date():
            raise ValidationError('Hire date cannot be in the future.')
        return hire_date

    def clean_termination_date(self):
        termination_date = self.cleaned_data.get('termination_date')
        hire_date = self.cleaned_data.get('hire_date')
        
        if termination_date:
            if hire_date and termination_date < hire_date:
                raise ValidationError('Termination date cannot be before hire date.')
            if termination_date > timezone.now().date():
                raise ValidationError('Termination date cannot be in the future.')
        
        return termination_date

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data.get('date_of_birth')
        if date_of_birth:
            age = (timezone.now().date() - date_of_birth).days // 365
            if age < 16:
                raise ValidationError('Employee must be at least 16 years old.')
            if age > 100:
                raise ValidationError('Please check the date of birth.')
        return date_of_birth

    def clean_salary(self):
        salary = self.cleaned_data['salary']
        if salary <= 0:
            raise ValidationError('Salary must be greater than zero.')
        if salary > 10000000:  # 10 million limit
            raise ValidationError('Salary seems unreasonably high. Please verify.')
        return salary


class EmployeeSearchForm(forms.Form):
    """Form for searching employees"""
    
    search_query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, email, or employee ID...'
        })
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label="All Departments",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        required=False,
        empty_label="All Positions",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    employment_status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Employee.EMPLOYMENT_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class DepartmentForm(forms.ModelForm):
    """Form for creating and editing departments"""
    
    class Meta:
        model = Department
        fields = ['name', 'description', 'manager']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = Employee.objects.filter(employment_status='active')


class PositionForm(forms.ModelForm):
    """Form for creating and editing positions"""
    
    class Meta:
        model = Position
        fields = ['title', 'description', 'salary_min', 'salary_max']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')

        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError('Minimum salary cannot be greater than maximum salary.')

        return cleaned_data


class EmployeeDocumentForm(forms.ModelForm):
    """Form for uploading employee documents"""
    
    class Meta:
        model = EmployeeDocument
        fields = ['document_type', 'title', 'description', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class EmployeeNoteForm(forms.ModelForm):
    """Form for adding employee notes"""
    
    class Meta:
        model = EmployeeNote
        fields = ['title', 'content', 'is_confidential']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class GeofenceForm(forms.ModelForm):
    """Form for creating and editing geofences"""
    
    class Meta:
        model = Geofence
        fields = ['name', 'description', 'center_latitude', 'center_longitude', 'radius', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter geofence name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter description (optional)'
            }),
            'center_latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'placeholder': 'e.g., 40.7128'
            }),
            'center_longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 'any',
                'placeholder': 'e.g., -74.0060'
            }),
            'radius': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Radius in meters'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'center_latitude': 'Center Latitude',
            'center_longitude': 'Center Longitude',
            'radius': 'Radius (meters)',
            'is_active': 'Active'
        }
    
    def clean_center_latitude(self):
        latitude = self.cleaned_data['center_latitude']
        if not -90 <= latitude <= 90:
            raise forms.ValidationError('Latitude must be between -90 and 90 degrees.')
        return latitude
    
    def clean_center_longitude(self):
        longitude = self.cleaned_data['center_longitude']
        if not -180 <= longitude <= 180:
            raise forms.ValidationError('Longitude must be between -180 and 180 degrees.')
        return longitude
    
    def clean_radius(self):
        radius = self.cleaned_data['radius']
        if radius <= 0:
            raise forms.ValidationError('Radius must be greater than 0.')
        if radius > 10000:  # 10km limit
            raise forms.ValidationError('Radius cannot exceed 10,000 meters.')
        return radius

