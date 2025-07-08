# HR-Max AI Assistant Integration - Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the HR-Max system with AI assistant integration to a production environment.

## Prerequisites

### System Requirements
- **Operating System:** Ubuntu 20.04+ or CentOS 8+
- **Python:** 3.9+
- **Database:** PostgreSQL 12+ (recommended) or MySQL 8.0+
- **Memory:** 4GB RAM minimum, 8GB recommended
- **Storage:** 20GB minimum, 50GB recommended
- **Network:** HTTPS support required

### Required Services
- **Web Server:** Nginx or Apache
- **WSGI Server:** Gunicorn or uWSGI
- **ASGI Server:** Daphne or Uvicorn (for WebSocket support)
- **Cache:** Redis (recommended for production)
- **Message Queue:** Redis or RabbitMQ
- **SSL Certificate:** Let's Encrypt or commercial certificate

## Installation Steps

### 1. System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

# Create application user
sudo useradd -m -s /bin/bash hrmax
sudo usermod -aG sudo hrmax
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE hrmax_production;
CREATE USER hrmax_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE hrmax_production TO hrmax_user;
ALTER USER hrmax_user CREATEDB;
\q
```

### 3. Application Deployment

```bash
# Switch to application user
sudo su - hrmax

# Create application directory
mkdir -p /home/hrmax/apps/hrmax
cd /home/hrmax/apps/hrmax

# Extract application files
tar -xzf hr-max-system.tar.gz
cd hr-max

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn daphne psycopg2-binary redis
```

### 4. Configuration

#### Environment Variables
Create `/home/hrmax/apps/hrmax/hr-max/.env`:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your_very_secure_secret_key_here
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database Configuration
DATABASE_URL=postgresql://hrmax_user:secure_password_here@localhost:5432/hrmax_production

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Security Settings
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Email Configuration (for notifications)
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@domain.com
EMAIL_HOST_PASSWORD=your_email_password
```

#### Django Settings Update
Update `hrmax/settings.py` for production:

```python
import os
from pathlib import Path
import dj_database_url

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Security settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database configuration
DATABASES = {
    'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
}

# Redis configuration for channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [os.getenv('REDIS_URL', 'redis://localhost:6379/0')],
        },
    },
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Security settings
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/home/hrmax/logs/django.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/home/hrmax/logs/security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'hr.api_views': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 5. Database Migration

```bash
# Run migrations
source venv/bin/activate
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup HR permissions
python manage.py setup_hr_permissions

# Collect static files
python manage.py collectstatic --noinput
```

### 6. Service Configuration

#### Gunicorn Configuration
Create `/home/hrmax/apps/hrmax/hr-max/gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "hrmax"
group = "hrmax"
tmp_upload_dir = None
errorlog = "/home/hrmax/logs/gunicorn_error.log"
accesslog = "/home/hrmax/logs/gunicorn_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
loglevel = "info"
```

#### Daphne Configuration for WebSockets
Create `/home/hrmax/apps/hrmax/hr-max/daphne.conf.py`:

```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrmax.settings')

from django.core.asgi import get_asgi_application
application = get_asgi_application()
```

#### Systemd Service Files

Create `/etc/systemd/system/hrmax-gunicorn.service`:

```ini
[Unit]
Description=HR-Max Gunicorn daemon
After=network.target

[Service]
User=hrmax
Group=hrmax
WorkingDirectory=/home/hrmax/apps/hrmax/hr-max
ExecStart=/home/hrmax/apps/hrmax/hr-max/venv/bin/gunicorn --config gunicorn.conf.py hrmax.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/hrmax-daphne.service`:

```ini
[Unit]
Description=HR-Max Daphne daemon for WebSockets
After=network.target

[Service]
User=hrmax
Group=hrmax
WorkingDirectory=/home/hrmax/apps/hrmax/hr-max
ExecStart=/home/hrmax/apps/hrmax/hr-max/venv/bin/daphne -b 127.0.0.1 -p 8001 hrmax.asgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 7. Nginx Configuration

Create `/etc/nginx/sites-available/hrmax`:

```nginx
upstream hrmax_app {
    server 127.0.0.1:8000;
}

upstream hrmax_websocket {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    client_max_body_size 10M;

    # Static files
    location /static/ {
        alias /home/hrmax/apps/hrmax/hr-max/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/hrmax/apps/hrmax/hr-max/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://hrmax_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Login endpoint with stricter rate limiting
    location /login/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://hrmax_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket connections
    location /ws/ {
        proxy_pass http://hrmax_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Main application
    location / {
        proxy_pass http://hrmax_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 8. Service Startup

```bash
# Create log directories
sudo mkdir -p /home/hrmax/logs
sudo chown hrmax:hrmax /home/hrmax/logs

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable hrmax-gunicorn hrmax-daphne
sudo systemctl start hrmax-gunicorn hrmax-daphne

# Enable and configure nginx
sudo ln -s /etc/nginx/sites-available/hrmax /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## Monitoring and Maintenance

### Log Monitoring

```bash
# Application logs
tail -f /home/hrmax/logs/django.log
tail -f /home/hrmax/logs/security.log

# Service logs
sudo journalctl -u hrmax-gunicorn -f
sudo journalctl -u hrmax-daphne -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Health Checks

Create `/home/hrmax/scripts/health_check.sh`:

```bash
#!/bin/bash

# Check application health
curl -f http://localhost:8000/admin/ > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Application health check failed"
    sudo systemctl restart hrmax-gunicorn
fi

# Check WebSocket health
curl -f http://localhost:8001/ > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "WebSocket health check failed"
    sudo systemctl restart hrmax-daphne
fi

# Check database connectivity
sudo -u hrmax /home/hrmax/apps/hrmax/hr-max/venv/bin/python /home/hrmax/apps/hrmax/hr-max/manage.py check --database default
```

### Backup Strategy

Create `/home/hrmax/scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/hrmax/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U hrmax_user hrmax_production > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /home/hrmax/apps/hrmax/hr-max/media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Performance Monitoring

Install and configure monitoring tools:

```bash
# Install monitoring packages
pip install django-prometheus psutil

# Add to Django settings
INSTALLED_APPS += ['django_prometheus']
MIDDLEWARE = ['django_prometheus.middleware.PrometheusBeforeMiddleware'] + MIDDLEWARE + ['django_prometheus.middleware.PrometheusAfterMiddleware']
```

## Security Checklist

- [ ] SSL/TLS certificate installed and configured
- [ ] Security headers configured in Nginx
- [ ] Rate limiting enabled for API endpoints
- [ ] Database credentials secured
- [ ] Django SECRET_KEY is unique and secure
- [ ] DEBUG mode disabled in production
- [ ] Firewall configured to allow only necessary ports
- [ ] Regular security updates scheduled
- [ ] Backup strategy implemented and tested
- [ ] Log monitoring configured
- [ ] Health checks implemented

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if Gunicorn service is running
   - Verify socket permissions
   - Check application logs

2. **WebSocket Connection Failed**
   - Verify Daphne service is running
   - Check Redis connectivity
   - Verify Nginx WebSocket configuration

3. **Database Connection Error**
   - Check PostgreSQL service status
   - Verify database credentials
   - Check network connectivity

4. **Static Files Not Loading**
   - Run `python manage.py collectstatic`
   - Check Nginx static file configuration
   - Verify file permissions

### Performance Issues

1. **Slow API Responses**
   - Check database query performance
   - Monitor Redis cache hit rates
   - Review application logs for bottlenecks

2. **High Memory Usage**
   - Adjust Gunicorn worker count
   - Monitor Django memory usage
   - Check for memory leaks

## Support

For technical support or deployment assistance, please refer to:
- Application logs in `/home/hrmax/logs/`
- System logs via `journalctl`
- Django admin interface for system status
- API documentation for integration details

---
*Deployment Guide Version: 1.0*
*Last Updated: June 10, 2025*
*Compatible with: HR-Max v2.0+ with AI Assistant Integration*

