# ChequeDB - Cheque Management System

A modern Django-based dashboard application for managing and processing cheques in queue. Built with a sophisticated UI featuring a responsive sidebar, real-time status tracking, and cheque pipeline management.

## Project Overview

**ChequeDB** is a comprehensive cheque processing management system designed to streamline cheque operations through an intuitive dashboard interface. It provides real-time tracking of:

- Cheques in queue
- Approved cheques
- Rejected cheques  
- Processing time metrics
- Service health status

## Tech Stack

- **Backend**: Django 6.0.7 with PostgreSQL ORM
- **Database**: PostgreSQL 12+ with UUID support
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **UI Framework**: Bootstrap 5.3.3 + Custom Design System
- **Icons**: Bootstrap Icons 1.11.3
- **Fonts**: Space Grotesk, Inter, IBM Plex Mono
- **Database Driver**: psycopg2-binary for Python-PostgreSQL connection

## Project Structure

```
ChequeSystem/
├── config/                          # Django project configuration
│   ├── settings.py                 # Project settings
│   ├── urls.py                     # URL routing configuration
│   ├── asgi.py                     # ASGI application
│   ├── wsgi.py                     # WSGI application
│   └── static/                     # Static files (CSS, JS)
│       ├── css/
│       │   └── dashboard.css       # Dashboard styling
│       └── js/
│           └── dashboard.js        # Dashboard interactions
│
├── dashboard/                       # Django app for dashboard
│   ├── models.py                   # Database models
│   ├── views.py                    # View functions
│   ├── urls.py                     # App-level URL routing
│   ├── admin.py                    # Django admin configuration
│   ├── apps.py                     # App configuration
│   ├── migrations/                 # Database migrations
│   └── templates/
│       └── dashboard/
│           └── dashboard.html      # Main dashboard template
│
├── manage.py                        # Django management script
├── db.sqlite3                       # Legacy SQLite (use PostgreSQL instead)
├── requirements.txt                 # Python dependencies
├── DATABASE_SETUP.md                # PostgreSQL setup guide
└── QUICKSTART.md                    # Quick start guide with examples
```

## Database Architecture

**ChequeDB** now uses **PostgreSQL** with a comprehensive relational schema:

| Table | Purpose |
|-------|---------|
| `cheques` | Main cheque documents with OCR results |
| `cheque_images` | Cheque image storage (front/back/UV) |
| `ocr_data` | Extracted OCR field data with confidence scores |
| `processing_queue` | Workflow queue with priority and assignment |
| `status_history` | Audit trail of all status changes |
| `audit_log` | Complete audit log for compliance |
| `users` | User management and roles |

See [DATABASE_SETUP.md](DATABASE_SETUP.md) for detailed schema information.

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL 12+ (installed and running)
- pip (Python package manager)

### Quick Start (5 Minutes)

For a quick setup with sample data, see [QUICKSTART.md](QUICKSTART.md)

### Detailed Setup

#### 1. Create PostgreSQL Database

```bash
psql -U postgres

# In PostgreSQL prompt:
CREATE DATABASE cheque_system_db;
\c cheque_system_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This includes:
- Django 6.0.7
- psycopg2-binary (PostgreSQL adapter)
- Other required packages

#### 3. Apply Database Migrations

```bash
python manage.py migrate
```

This creates all tables defined in the models:
- cheques
- cheque_images
- ocr_data
- processing_queue
- status_history
- audit_log
- auth (Django built-in)
- sessions (Django built-in)

#### 4. Load Sample Data (Optional)

```bash
python manage.py load_sample_data
```

This loads 5 sample cheques with OCR data for testing.

#### 5. Create Admin Superuser (Optional)

```bash
python manage.py createsuperuser
```

#### 6. Run Development Server

```bash
python manage.py runserver
```

Access the application:
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Queue**: http://127.0.0.1:8000/dashboard/queue/
- **Cheque Detail**: Click eye icon on queue table
- **Admin Panel**: http://127.0.0.1:8000/admin/ (with superuser)

## Key Features

### Dashboard Interface
- **Stat Cards (Cheque Stubs)**: Visual "torn cheque stub" design for metrics display
- **Service Status Panel**: Real-time health monitoring of API, OCR, and Bank Sync services
- **Charts & Analytics**: 7-day cheque processing trends and queue breakdown visualization
- **Queue Table**: Real-time queue status with filtering by status (Pending, Approved, Rejected)
- **Cheque Details**: Professional detail view with OCR data and match indicators

### Database Features
- **UUID Primary Keys**: Unique identifiers for all records
- **Soft Deletes**: Mark cheques as deleted without removing data
- **Audit Trail**: Complete history of all changes via StatusHistory table
- **OCR Tracking**: Confidence scores for each extracted field
- **Processing Queue**: Priority-based workflow with assignment tracking
- **Comprehensive Auditing**: Full audit log of actions performed by users

### Data Models

#### Cheques
- Stores main cheque information
- Tracks processing status (pending/approved/rejected)
- Stores OCR match status (match/mismatch/pending)
- Soft delete capability for data retention
- Version control for updates

#### ChequeImages
- Stores multiple images per cheque (front, back, UV)
- File path and size tracking
- Linked to cheque via foreign key

#### OCRData
- Extracted field data from OCR machine
- Confidence scores (0-100) for each field
- Supports multiple fields per cheque
- Unique constraint on cheque + field combination

#### ProcessingQueue
- Tracks workflow state
- Priority-based ordering
- User assignment tracking
- Timestamps for picked and completed states

#### StatusHistory
- Audit trail of status changes
- User tracking (who changed the status)
- Remarks/comments on changes
- Immutable records (no updates)

#### AuditLog
- Comprehensive logging of all changes
- JSON storage of old/new values
- Action tracking (create/update/delete/approve/reject)
- User attribution

### UI/UX Features
- 🌓 **Dark/Light Mode**: Toggle theme with local storage persistence
- 📱 **Responsive Design**: Mobile-first approach with sidebar collapse on desktop
- ⌚ **Status Indicators**: Visual indicators for cheque states (Pending, Approved, Rejected)
- 👁️ **Detail Page**: Click eye icon to view full cheque details with OCR data
- 🎨 **Design System**: 
  - Brand colors with HSL-based variables
  - Consistent spacing, typography, and shadows
  - Color-coded status badges (Match, Mismatch, Pending)

### Navigation
- Sidebar with workspace sections (Dashboard, Upload, Queue, Approval)
- Reports section (Analytics, Settings)
- Mobile drawer menu for small screens
- Search functionality for cheque lookups
- Quick navigation between dashboard and queue

## Fixed Issues & Improvements

### Original Issues (Now Resolved)
1. ✅ **URL Configuration Error**: Changed URL pattern from `'blog.urls'` to `'dashboard.urls'`
2. ✅ **Missing Dashboard URLs**: Created `dashboard/urls.py` with proper routing
3. ✅ **Empty Views**: Implemented view functions to render templates
4. ✅ **Template Path**: Updated TEMPLATES settings to look in `dashboard/templates/`
5. ✅ **Template Directory**: Created proper template structure
6. ✅ **Static Files**: Fixed static file references using Django's `{% static %}` template tag
7. ✅ **Dependencies**: Generated requirements.txt with all packages

### Database Integration (New)
8. ✅ **Database Migration**: Upgraded from SQLite to PostgreSQL
9. ✅ **Model Architecture**: Implemented comprehensive relational schema
10. ✅ **Views Updated**: Views now query database instead of mock data
11. ✅ **Admin Interface**: Full Django admin interface with custom configuration
12. ✅ **Audit Trail**: Complete logging system for compliance
13. ✅ **Data Validation**: Model validation and constraints in place
14. ✅ **Management Commands**: Custom commands for data loading

## Admin Interface

Access Django admin at: **http://127.0.0.1:8000/admin/**

The admin interface includes:
- **Cheques**: Add, edit, search, filter by status/match
- **ChequeImages**: Manage cheque images (front/back/UV)
- **OCRData**: View extracted OCR fields with confidence scores
- **ProcessingQueue**: Track workflow state and assignments
- **StatusHistory**: View complete audit trail
- **AuditLog**: Complete action history with change tracking

Color-coded status badges help identify cheque states at a glance.

## File Changes

### config/urls.py
```python
# Before: path('dashboard/', include('blog.urls'))
# After:  path('dashboard/', include('dashboard.urls'))
```

### config/settings.py
```python
# Updated TEMPLATES DIRS
'DIRS': [BASE_DIR / 'dashboard' / 'templates'],
```

### dashboard/urls.py
Created with single route:
```python
path('', views.dashboard, name='dashboard')
```

### dashboard/views.py
Implemented dashboard view to render template

### dashboard/templates/dashboard/dashboard.html
Created with proper Django template tags for static files

## Admin Interface

Access Django admin at: **http://127.0.0.1:8000/admin/**

Default credentials can be set by creating a superuser:
```bash
python manage.py createsuperuser
```

## Commands Reference

| Command | Purpose |
|---------|---------|
| `python manage.py runserver` | Start development server (default port 8000) |
| `python manage.py migrate` | Apply database migrations |
| `python manage.py makemigrations` | Create new migrations based on model changes |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py shell` | Interactive Python shell with Django context |
| `python manage.py test` | Run test suite |
| `python manage.py collectstatic` | Collect static files for production |

## Development Notes

### Adding Models
1. Define models in `dashboard/models.py`
2. Create migrations: `python manage.py makemigrations`
3. Apply migrations: `python manage.py migrate`

### Adding Views
1. Create view functions in `dashboard/views.py`
2. Add URL patterns in `dashboard/urls.py`
3. Create templates in `dashboard/templates/dashboard/`

### Styling
- Global styles: `config/static/css/dashboard.css`
- Custom design system with CSS variables
- Bootstrap utilities for layout

### JavaScript
- Sidebar collapse/expand functionality
- Theme toggle (dark/light mode)
- Mobile drawer menu
- Navigation active state management

## Current Status

✅ **Project is fully runnable**

- Server starts without errors
- Database initialized with migrations
- Dashboard template renders correctly
- All static files properly referenced
- Ready for feature development

## Next Steps

To extend the project:

1. **Create Cheque Model**: Define database schema for cheques
2. **Implement Data Views**: Update dashboard with real database data
3. **Add Upload Feature**: Implement cheque upload functionality
4. **Create Queue Management**: Implement queue operations
5. **Add Authentication**: Secure dashboard with login
6. **Deploy**: Set up production environment with proper WSGI server

## Production Deployment

For production deployment:

1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS` with actual domain
3. Use production WSGI server (Gunicorn, uWSGI)
4. Set up environment variables for secrets
5. Use PostgreSQL instead of SQLite
6. Configure static file serving via CDN or nginx
7. Enable HTTPS

## Support

For issues or questions about this project, refer to:
- Django Documentation: https://docs.djangoproject.com/
- Bootstrap Documentation: https://getbootstrap.com/
- Project conventions documented throughout codebase

---

**Project Status**: Ready for Development  
**Last Updated**: July 15, 2026  
**Django Version**: 6.0.7  
**Python Version**: 3.10+
