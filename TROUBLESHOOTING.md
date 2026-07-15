# ChequeDB - Troubleshooting Guide

## Common Issues and Solutions

### 1. "ModuleNotFoundError: No module named 'django'"

**Problem**: Django is not installed in your Python environment.

**Solution**:
```bash
pip install django
# or install from requirements.txt
pip install -r requirements.txt
```

---

### 2. "No such file or directory: 'manage.py'"

**Problem**: Running the command from the wrong directory.

**Solution**: Always run Django commands from the `ChequeSystem` folder:
```bash
cd d:\ChequeSystemProject\ChequeSystem
python manage.py runserver 8000
```

---

### 3. "django.core.exceptions.ImproperlyConfigured" or settings errors

**Problem**: Django settings not configured properly or app not in INSTALLED_APPS.

**Solution**: 
- Verify `dashboard` is in `INSTALLED_APPS` in [config/settings.py](config/settings.py#L36)
- Check that `ROOT_URLCONF = 'config.urls'` is set
- Ensure database migrations are applied: `python manage.py migrate`

---

### 4. "TemplateDoesNotExist" error

**Problem**: Template file not found at expected location.

**Solution**:
- Verify template exists at: `dashboard/templates/dashboard/dashboard.html`
- Check TEMPLATES DIRS in settings.py include the correct path
- Ensure you're using `{% load static %}` tag and `{% static 'path/to/file' %}` for static files

---

### 5. Static files (CSS/JS) not loading

**Problem**: Browser shows unstyled dashboard.

**Solution**:
- Run `python manage.py collectstatic` (for production)
- For development, Django serves static files automatically
- Verify static files are in: `config/static/css/` and `config/static/js/`
- Check browser console (F12) for 404 errors on static files
- Ensure templates use `{% load static %}` and `{% static 'path' %}`

**Development Server Static Files**:
```python
# Already configured in config/settings.py
STATIC_URL = 'static/'
```

---

### 6. "port 8000 is already in use"

**Problem**: Another process is using port 8000.

**Solution**: Use a different port:
```bash
python manage.py runserver 8001
```

Or find and kill the existing process using port 8000.

---

### 7. Database errors or missing tables

**Problem**: "no such table" or database-related errors.

**Solution**:
```bash
python manage.py migrate
```

If you've modified models:
```bash
python manage.py makemigrations
python manage.py migrate
```

To start fresh:
```bash
# Delete db.sqlite3
rm db.sqlite3
# Re-run migrations
python manage.py migrate
```

---

### 8. CSRF token error on form submission

**Problem**: "CSRF token missing or incorrect"

**Solution**: Ensure the template includes:
```html
{% csrf_token %}
```

inside any `<form>` tag.

---

### 9. Admin panel shows 404 error

**Problem**: Can't access `/admin/`

**Solution**:
- Verify URLs are configured in [config/urls.py](config/urls.py)
- Admin should be pre-configured and working
- Try creating a superuser: `python manage.py createsuperuser`
- Access at: `http://127.0.0.1:8000/admin/`

---

### 10. Browser shows blank page or 404 at dashboard

**Problem**: Dashboard URL returns 404 Not Found

**Solution**:
- Verify URL in browser: `http://127.0.0.1:8000/dashboard/`
- Check that [dashboard/urls.py](dashboard/urls.py) exists with proper routes
- Verify [config/urls.py](config/urls.py) includes dashboard URLs
- Run `python manage.py check` to validate configuration

---

## Debugging Steps

### 1. Check Django System Status
```bash
python manage.py check
```

This performs system checks and reports any issues.

---

### 2. Enable Debug Output
Add debug info to see more detailed error messages:

```python
# In config/settings.py
DEBUG = True  # Already set for development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

---

### 3. Check File Permissions
Windows: Ensure files aren't read-only
```bash
# Clear read-only attribute
attrib -R d:\ChequeSystemProject\ChequeSystem\* /S
```

---

### 4. Use Django Shell
```bash
python manage.py shell
```

Test database connections and model queries interactively.

---

### 5. View Server Logs
Keep the development server running in a terminal to see real-time logs:
```bash
python manage.py runserver 8000
```

Error messages appear in the terminal output.

---

## Environment Variables

For production, create a `.env` file and set:
```
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:password@localhost/dbname
```

Load environment variables in [config/settings.py](config/settings.py):
```python
from decouple import config

SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
```

Install python-decouple:
```bash
pip install python-decouple
```

---

## Performance Tips

1. **Cache**: Enable caching for better performance
2. **Database**: Use PostgreSQL instead of SQLite for production
3. **Assets**: Minify CSS/JS files
4. **Compression**: Enable GZIP compression
5. **Pagination**: Limit query results for large datasets

---

## Getting Help

- Django Documentation: https://docs.djangoproject.com/
- Django Community: https://www.djangoproject.com/community/
- Stack Overflow: Search `django` and your error message
- GitHub Issues: Check project repository

---

**Last Updated**: July 15, 2026
