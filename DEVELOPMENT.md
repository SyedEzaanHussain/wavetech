# ChequeDB - Development Guide

## Development Workflow

### Initial Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Apply Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser (Optional)**
   ```bash
   python manage.py createsuperuser
   ```

4. **Start Development Server**
   ```bash
   python manage.py runserver 8000
   ```

### Development Server

The Django development server automatically:
- Reloads on code changes
- Serves static files
- Displays debug information

Access points:
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Admin Panel**: http://127.0.0.1:8000/admin/

---

## Project Architecture

### Django App Structure

```
dashboard/
├── models.py         # Database models
├── views.py          # View logic
├── urls.py           # URL routing
├── admin.py          # Admin interface config
├── tests.py          # Unit tests
├── migrations/       # Database migrations
└── templates/        # HTML templates
    └── dashboard/
        └── dashboard.html
```

### Configuration

```
config/
├── settings.py       # Project settings
├── urls.py           # Project-level routing
├── wsgi.py           # Production WSGI app
├── asgi.py           # ASGI config
└── static/           # Static assets
    ├── css/
    └── js/
```

---

## Adding Features

### 1. Creating a New Model

**File**: `dashboard/models.py`

```python
from django.db import models

class Cheque(models.Model):
    """Database model for cheque records"""
    
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    
    cheque_id = models.CharField(max_length=20, unique=True)
    payee = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Cheques'
    
    def __str__(self):
        return f"{self.cheque_id} - {self.payee}"
```

### 2. Create Migrations

After creating models:

```bash
python manage.py makemigrations
python manage.py migrate
```

Files created automatically:
- `dashboard/migrations/0001_initial.py`

### 3. Register in Admin

**File**: `dashboard/admin.py`

```python
from django.contrib import admin
from .models import Cheque

@admin.register(Cheque)
class ChequeAdmin(admin.ModelAdmin):
    list_display = ('cheque_id', 'payee', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('cheque_id', 'payee')
    readonly_fields = ('created_at', 'updated_at')
```

### 4. Create Views

**File**: `dashboard/views.py`

```python
from django.shortcuts import render
from .models import Cheque

def dashboard(request):
    """Render dashboard with real data"""
    context = {
        'cheques_in_queue': Cheque.objects.filter(status='pending').count(),
        'approved_cheques': Cheque.objects.filter(status='approved').count(),
        'rejected_cheques': Cheque.objects.filter(status='rejected').count(),
        'recent_cheques': Cheque.objects.all()[:5],
    }
    return render(request, 'dashboard/dashboard.html', context)

def cheque_list(request):
    """List all cheques with filtering"""
    status = request.GET.get('status')
    cheques = Cheque.objects.all()
    
    if status:
        cheques = cheques.filter(status=status)
    
    context = {
        'cheques': cheques,
        'status_filter': status,
    }
    return render(request, 'dashboard/cheque_list.html', context)
```

### 5. Update URLs

**File**: `dashboard/urls.py`

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cheques/', views.cheque_list, name='cheque_list'),
]
```

### 6. Create Templates

**File**: `dashboard/templates/dashboard/cheque_list.html`

```html
{% extends 'dashboard/dashboard.html' %}
{% load static %}

{% block content %}
<div class="page-heading">
    <h1>Cheques</h1>
    <p>All cheques in the system</p>
</div>

<div class="table-responsive">
    <table class="cheque-table">
        <thead>
            <tr>
                <th>Cheque ID</th>
                <th>Payee</th>
                <th>Amount</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for cheque in cheques %}
            <tr>
                <td>{{ cheque.cheque_id }}</td>
                <td>{{ cheque.payee }}</td>
                <td>Rs. {{ cheque.amount }}</td>
                <td>{{ cheque.get_status_display }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

---

## Styling & CSS

### Design System Variables

**File**: `config/static/css/dashboard.css`

CSS custom properties (variables) for consistency:

```css
:root {
  /* Brand Colors */
  --primary-h: 271;
  --primary-s: 81%;
  --primary-l: 56%;
  --primary: hsl(var(--primary-h) var(--primary-s) var(--primary-l));
  
  /* Status Colors */
  --mint: #0FA968;
  --rose: #E4384C;
  --amber: #D98A15;
  --sky: #2E7BD6;
  
  /* Neutrals */
  --ink: #17151F;
  --paper: #F6F5FA;
  --surface: #FFFFFF;
  
  /* Components */
  --radius: 14px;
  --shadow-card: 0 1px 2px rgba(23, 21, 31, 0.04);
}

[data-theme="dark"] {
  --ink: #F3F1FA;
  --paper: #1A171F;
  --surface: #2A2735;
}
```

### Adding Custom Styles

```css
/* Create new component styles */
.custom-component {
  background: var(--surface);
  border-radius: var(--radius);
  box-shadow: var(--shadow-card);
  padding: 1.5rem;
}
```

---

## JavaScript Enhancement

### Adding Interactivity

**File**: `config/static/js/dashboard.js`

```javascript
// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
  const filterButtons = document.querySelectorAll('.filter-chip');
  
  filterButtons.forEach(button => {
    button.addEventListener('click', function() {
      // Handle filter logic
      console.log('Filter:', this.textContent);
    });
  });
});

// Utility function
function showNotification(message, type = 'success') {
  const toast = document.getElementById('toast');
  const msg = document.getElementById('toastMsg');
  msg.textContent = message;
  toast.classList.add(`toast-${type}`);
  toast.classList.add('show');
  
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}
```

---

## Testing

### Unit Tests

**File**: `dashboard/tests.py`

```python
from django.test import TestCase
from .models import Cheque

class ChequeModelTest(TestCase):
    def setUp(self):
        self.cheque = Cheque.objects.create(
            cheque_id='CHQ-001',
            payee='Test Company',
            amount=1000.00,
            status=Cheque.PENDING
        )
    
    def test_cheque_creation(self):
        self.assertEqual(self.cheque.payee, 'Test Company')
        self.assertEqual(self.cheque.status, Cheque.PENDING)
    
    def test_cheque_string_representation(self):
        self.assertEqual(str(self.cheque), 'CHQ-001 - Test Company')
```

### Run Tests

```bash
python manage.py test
python manage.py test dashboard  # Run only dashboard tests
python manage.py test dashboard.tests.ChequeModelTest
```

---

## API Development

### Creating Django REST API

Install Django REST Framework:
```bash
pip install djangorestframework
```

Create serializers:

```python
# dashboard/serializers.py
from rest_framework import serializers
from .models import Cheque

class ChequeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cheque
        fields = ['id', 'cheque_id', 'payee', 'amount', 'status', 'created_at']
```

Create API views:

```python
# dashboard/views.py
from rest_framework import viewsets
from .models import Cheque
from .serializers import ChequeSerializer

class ChequeViewSet(viewsets.ModelViewSet):
    queryset = Cheque.objects.all()
    serializer_class = ChequeSerializer
```

Register in URLs:

```python
# dashboard/urls.py
from rest_framework.routers import DefaultRouter
from .views import ChequeViewSet

router = DefaultRouter()
router.register(r'api/cheques', ChequeViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

---

## Database Management

### Backing Up Database

```bash
# SQLite - just copy the file
cp db.sqlite3 db.sqlite3.backup
```

### Inspecting Database

```bash
python manage.py dbshell
```

### Database Optimization

```bash
# Analyze query performance
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> with CaptureQueriesContext(connection) as context:
...     # Your code here
>>> print(f"Total queries: {len(context)}")
>>> for query in context:
...     print(query['sql'])
```

---

## Deployment Preparation

### Production Checklist

- [ ] Set `DEBUG = False`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set `SECURE_SSL_REDIRECT = True`
- [ ] Enable `HSTS` headers
- [ ] Configure CSRF settings
- [ ] Use PostgreSQL instead of SQLite
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Configure email backend
- [ ] Set up logging
- [ ] Use environment variables for secrets

### Deployment Settings

```python
# config/settings.py for production

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Static files with CDN
STATIC_URL = 'https://cdn.yourdomain.com/static/'
STATIC_ROOT = '/var/www/static/'
```

---

## Useful Django Commands

| Command | Purpose |
|---------|---------|
| `python manage.py shell` | Interactive Python shell with Django context |
| `python manage.py shell_plus` | Enhanced shell (requires django-extensions) |
| `python manage.py check` | Validate configuration |
| `python manage.py makemigrations` | Create migration files |
| `python manage.py migrate` | Apply migrations |
| `python manage.py showmigrations` | List migration status |
| `python manage.py sqlmigrate` | Show SQL for migration |
| `python manage.py test` | Run tests |
| `python manage.py collectstatic` | Gather static files |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py changepassword` | Change user password |
| `python manage.py dumpdata` | Export data to JSON |
| `python manage.py loaddata` | Import data from JSON |
| `python manage.py dbshell` | Open database shell |

---

## Resources

- **Django Docs**: https://docs.djangoproject.com/
- **Django ORM**: https://docs.djangoproject.com/en/6.0/topics/db/models/
- **Django Forms**: https://docs.djangoproject.com/en/6.0/topics/forms/
- **Django Admin**: https://docs.djangoproject.com/en/6.0/ref/contrib/admin/
- **Django Security**: https://docs.djangoproject.com/en/6.0/topics/security/
- **Django Testing**: https://docs.djangoproject.com/en/6.0/topics/testing/
- **DRF Documentation**: https://www.django-rest-framework.org/

---

**Version**: 1.0  
**Last Updated**: July 15, 2026  
**Django Version**: 6.0.7
