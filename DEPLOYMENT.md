# HR-Max Deployment Guide

## Quick Start (Development)

1. **Navigate to project directory:**
   ```bash
   cd hr-max
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Start the server:**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. **Access the system:**
   - URL: http://localhost:8000
   - Username: admin
   - Password: admin123

## Production Deployment Options

### Option 1: Simple Production Setup

1. **Install production dependencies:**
   ```bash
   pip install gunicorn psycopg2-binary
   ```

2. **Configure production settings:**
   ```python
   # In settings.py
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com', 'your-ip-address']
   
   # Use PostgreSQL
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'hrmax_db',
           'USER': 'hrmax_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

3. **Run with Gunicorn:**
   ```bash
   gunicorn hrmax.wsgi:application --bind 0.0.0.0:8000
   ```

### Option 2: Docker Deployment

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["gunicorn", "hrmax.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```

2. **Create requirements.txt:**
   ```
   Django==5.2.2
   gunicorn==21.2.0
   psycopg2-binary==2.9.7
   ```

3. **Build and run:**
   ```bash
   docker build -t hr-max .
   docker run -p 8000:8000 hr-max
   ```

### Option 3: Cloud Deployment (Heroku)

1. **Install Heroku CLI and login**

2. **Create Procfile:**
   ```
   web: gunicorn hrmax.wsgi:application --port $PORT
   ```

3. **Deploy:**
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku run python manage.py migrate
   heroku run python manage.py setup_hr_permissions
   heroku run python manage.py createsuperuser
   ```

## Environment Variables

Create a `.env` file for sensitive settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost/dbname
ALLOWED_HOSTS=your-domain.com,your-ip
```

## SSL/HTTPS Configuration

For production, always use HTTPS:

```python
# In settings.py for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

## Backup Strategy

### Database Backup
```bash
# PostgreSQL
pg_dump hrmax_db > backup_$(date +%Y%m%d_%H%M%S).sql

# SQLite
cp db.sqlite3 backup_$(date +%Y%m%d_%H%M%S).sqlite3
```

### Media Files Backup
```bash
tar -czf media_backup_$(date +%Y%m%d_%H%M%S).tar.gz media/
```

## Monitoring & Logging

### Basic Logging Setup
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'hrmax.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Performance Optimization

### Database Optimization
```python
# In settings.py
DATABASES = {
    'default': {
        # ... database config
        'OPTIONS': {
            'MAX_CONNS': 20,
            'CONN_MAX_AGE': 600,
        }
    }
}
```

### Caching
```python
# Redis caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## Security Checklist

- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS in production
- [ ] Set secure cookie settings
- [ ] Configure CSRF settings
- [ ] Set up proper file permissions
- [ ] Use environment variables for secrets
- [ ] Regular security updates
- [ ] Database access restrictions
- [ ] Backup encryption

## Troubleshooting

### Common Issues

1. **Static files not loading:**
   ```bash
   python manage.py collectstatic --noinput
   ```

2. **Database connection errors:**
   - Check database credentials
   - Verify database server is running
   - Check network connectivity

3. **Permission denied errors:**
   ```bash
   python manage.py setup_hr_permissions
   ```

4. **Migration issues:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Log Locations
- Application logs: `hrmax.log`
- Django logs: Check `LOGGING` configuration
- Web server logs: `/var/log/nginx/` or `/var/log/apache2/`

## Maintenance Tasks

### Daily
- Monitor system performance
- Check error logs
- Verify backup completion

### Weekly
- Review user access
- Check disk space
- Update dependencies (if needed)

### Monthly
- Security audit
- Performance review
- Database optimization
- Backup testing

## Support

For deployment assistance or issues:
1. Check the troubleshooting section
2. Review Django documentation
3. Contact the development team

---

**HR-Max Deployment Guide**  
*Version 1.0 - June 2025*

