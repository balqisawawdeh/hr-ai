# HR-Max Employee Management System

## Overview
HR-Max is a comprehensive Django-based employee management system designed for authorized HR personnel to efficiently access and manage employee information. The system features a modern, responsive design with robust authentication, input validation, and intuitive user interface.

## Features

### 🔐 Authentication & Authorization
- Secure login system for HR personnel
- Role-based access control (HR Personnel vs HR Managers)
- Custom permission system
- Session management

### 👥 Employee Management
- Complete employee profiles with personal, address, and employment information
- Employee search and filtering capabilities
- Document and note management for employees
- Manager-employee relationships
- Employment status tracking

### 🏢 Department Management
- Create and manage departments
- Assign department managers
- Track employee count per department

### 💼 Position Management
- Define job positions with salary ranges
- Track employees per position
- Position descriptions and requirements

### 📱 Responsive Design
- Mobile-first responsive design
- Modern Bootstrap 5 interface
- Touch-friendly navigation
- Professional gradient styling
- Smooth animations and transitions

### ✅ Form Validation
- Comprehensive client-side and server-side validation
- Real-time form feedback
- Data integrity enforcement
- User-friendly error messages

## Technology Stack

### Backend
- **Django 5.2.2** - Web framework
- **Python 3.11** - Programming language
- **SQLite** - Database (development)
- **Django Admin** - Administrative interface

### Frontend
- **HTML5** - Markup
- **CSS3** - Styling with custom variables and gradients
- **Bootstrap 5.3** - Responsive framework
- **JavaScript** - Interactive features
- **Font Awesome 6.4** - Icons

## Installation & Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or extract the project:**
   ```bash
   cd hr-max
   ```

2. **Create virtual environment:**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install django
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Set up HR permissions:**
   ```bash
   python manage.py setup_hr_permissions
   ```

6. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files:**
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Run development server:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

9. **Access the system:**
   - Main application: http://localhost:8000
   - Admin panel: http://localhost:8000/admin

## Default Credentials
- **Username:** admin
- **Password:** admin123
- **Email:** admin@hrmax.com

## User Roles & Permissions

### HR Personnel
- View employees, departments, and positions
- Search and filter employee data
- View employee documents and notes

### HR Managers
- All HR Personnel permissions plus:
- Add, edit, and delete employees
- Add, edit, and delete departments
- Add, edit, and delete positions
- Upload employee documents
- Add employee notes

### Super Administrator
- Full system access
- User management
- System configuration

## System Architecture

### Models
- **Employee** - Core employee information with relationships
- **Department** - Organizational departments
- **Position** - Job positions with salary ranges
- **EmployeeDocument** - File attachments for employees
- **EmployeeNote** - Notes and comments about employees

### Views
- **Authentication views** - Login/logout with custom decorators
- **Dashboard** - System overview and quick actions
- **Employee views** - CRUD operations with search/filter
- **Department views** - Department management
- **Position views** - Position management

### Templates
- **Base template** - Responsive layout with navigation
- **Authentication templates** - Login interface
- **HR templates** - Employee, department, and position interfaces
- **Form templates** - Reusable form layouts

## Security Features
- CSRF protection on all forms
- Input validation and sanitization
- Permission-based access control
- Secure password handling
- Session security

## Responsive Design Features
- Mobile-first approach
- Flexible grid layouts
- Touch-friendly interface
- Adaptive navigation
- Optimized for all screen sizes

## File Structure
```
hr-max/
├── hrmax/                 # Django project settings
│   ├── settings.py        # Configuration
│   ├── urls.py           # URL routing
│   └── wsgi.py           # WSGI configuration
├── hr/                   # Main HR application
│   ├── models.py         # Data models
│   ├── views.py          # View functions
│   ├── forms.py          # Form definitions
│   ├── admin.py          # Admin configuration
│   ├── auth_views.py     # Authentication views
│   └── management/       # Custom commands
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── registration/     # Auth templates
│   └── hr/              # HR templates
├── static/              # Static files
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript
├── media/               # User uploads
└── manage.py            # Django management
```

## Customization

### Adding New Fields
1. Update models in `hr/models.py`
2. Create and run migrations
3. Update forms in `hr/forms.py`
4. Update templates as needed

### Styling Changes
- Modify `static/css/style.css` for custom styles
- Update CSS variables for color scheme changes
- Customize Bootstrap components as needed

### Adding Features
1. Create new views in `hr/views.py`
2. Add URL patterns in `hr/urls.py`
3. Create templates in `templates/hr/`
4. Update navigation in `templates/base.html`

## Production Deployment

### Database
- Replace SQLite with PostgreSQL or MySQL
- Update `DATABASES` setting in `settings.py`
- Run migrations on production database

### Static Files
- Configure static file serving (nginx/Apache)
- Set `STATIC_ROOT` and `MEDIA_ROOT`
- Run `collectstatic` command

### Security
- Set `DEBUG = False`
- Configure `ALLOWED_HOSTS`
- Use environment variables for secrets
- Set up SSL/HTTPS

### Performance
- Configure caching
- Optimize database queries
- Set up monitoring and logging

## Support & Maintenance

### Regular Tasks
- Database backups
- Security updates
- Performance monitoring
- User access reviews

### Troubleshooting
- Check Django logs for errors
- Verify database connectivity
- Ensure static files are served correctly
- Validate user permissions

## License
This HR-Max system is proprietary software developed for internal use.

## Contact
For technical support or questions about the HR-Max system, please contact the development team.

---

**HR-Max Employee Management System**  
*Secure, Efficient, Professional*

