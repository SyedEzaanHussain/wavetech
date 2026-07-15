# Quick Start Guide - PostgreSQL Database Integration

## 🚀 Quick Setup (5 minutes)

### Step 1: Create PostgreSQL Database

**Windows PowerShell:**
```powershell
# Start PostgreSQL (if not running)
$env:PGPASSWORD='postgres'
psql -U postgres -h localhost

# Run these SQL commands:
CREATE DATABASE cheque_system_db;
\c cheque_system_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

**Linux/macOS Terminal:**
```bash
sudo -u postgres psql

# Run these SQL commands:
CREATE DATABASE cheque_system_db;
\c cheque_system_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

### Step 2: Install Dependencies

```bash
cd d:\ChequeSystemProject\ChequeSystem
pip install -r requirements.txt
```

### Step 3: Run Migrations

```bash
python manage.py migrate
```

Expected output:
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying dashboard.0001_initial... OK
  ...
```

### Step 4: Load Sample Data

```bash
python manage.py load_sample_data
```

Output:
```
🔄 Loading sample data...
✅ Created cheque: CHQ-10482 (JANIE GOULD)
✅ Created cheque: CHQ-10481 (AL-HABIB TRADERS)
...
🎉 Successfully loaded 5 sample cheques!
```

### Step 5: Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

Then access admin at: http://127.0.0.1:8000/admin/

### Step 6: Run Server

```bash
python manage.py runserver
```

Access the application:
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Queue**: http://127.0.0.1:8000/dashboard/queue/
- **Detail**: Click eye icon on any row

---

## 📊 Database Architecture

### Tables Overview

| Table | Purpose | Fields |
|-------|---------|--------|
| **cheques** | Main cheque documents | tracking_no, amount, beneficiary_name, status, match_status, ... |
| **cheque_images** | Cheque images (front/back/UV) | cheque_id, image_type, file_path, file_size |
| **ocr_data** | Extracted OCR fields | cheque_id, field_name, field_value, confidence_score |
| **processing_queue** | Workflow queue | cheque_id, queue_status, assigned_to, priority |
| **status_history** | Audit trail | cheque_id, old_status, new_status, remarks |
| **audit_log** | Complete audit log | table_name, action, performed_by, old/new_value (JSON) |

### Data Flow

```
Scanner → Insert into Cheques
           ↓
           → Store images in ChequeImages
           → Extract fields to OCRData
           → Add to ProcessingQueue
           ↓
User approves/rejects → Update Cheques.status
           ↓
           → Log change in StatusHistory
           → Log action in AuditLog
```

---

## 🔧 Common Tasks

### Add a New Cheque via Django Shell

```bash
python manage.py shell
```

```python
from dashboard.models import Cheque, OCRData
from decimal import Decimal
from datetime import date

# Create cheque
cheque = Cheque.objects.create(
    tracking_no='CHQ-10500',
    cheque_no='10500',
    amount=Decimal('5000.00'),
    beneficiary_name='YOUR COMPANY',
    cheque_date=date(2026, 7, 1),
    status='pending',
    match_status='pending'
)

# Add OCR data
OCRData.objects.create(
    cheque=cheque,
    field_name='amount',
    field_value='5000.00',
    confidence_score=Decimal('95.5')
)

exit()
```

### Update Cheque Status

```python
from dashboard.models import Cheque, StatusHistory
from django.contrib.auth.models import User

cheque = Cheque.objects.get(tracking_no='CHQ-10482')
user = User.objects.first()  # Get admin user

# Create history record
StatusHistory.objects.create(
    cheque=cheque,
    old_status=cheque.status,
    new_status='approved',
    changed_by=user,
    remarks='Manually approved'
)

# Update cheque
cheque.status = 'approved'
cheque.match_status = 'match'
cheque.save()
```

### Query Cheques

```python
from dashboard.models import Cheque

# All active cheques
active = Cheque.objects.active()

# By status
pending = Cheque.objects.pending()
approved = Cheque.objects.approved()
rejected = Cheque.objects.rejected()

# With OCR data
cheques_with_ocr = Cheque.objects.prefetch_related('ocr_data')

# With images
cheques_with_images = Cheque.objects.prefetch_related('images')

# Filtered query
high_value = Cheque.objects.filter(amount__gte=5000)
```

---

## 🐛 Troubleshooting

### PostgreSQL Connection Error

```
FATAL: password authentication failed for user "postgres"
```

**Solution:**
- Verify PostgreSQL is running
- Check connection string in `config/settings.py`
- Reset PostgreSQL password:
  ```bash
  # Windows: Open Services → PostgreSQL
  # In psql: ALTER USER postgres PASSWORD 'postgres';
  ```

### Database Does Not Exist

```
FATAL: database "cheque_system_db" does not exist
```

**Solution:**
```bash
psql -U postgres
CREATE DATABASE cheque_system_db;
\c cheque_system_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

### psycopg2 Installation Failed

```bash
# Windows
pip install psycopg2-binary

# macOS
brew install postgresql
pip install psycopg2

# Linux
sudo apt-get install postgresql-client libpq-dev
pip install psycopg2
```

### UUID Extension Not Available

```bash
psql -U postgres -d cheque_system_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
\q
```

---

## 📝 API Reference

### View: Queue List

**URL**: `/dashboard/queue/`
**Parameters**: `status=all|pending|approved|rejected`
**Returns**: 
- list of cheques with columns: system_id, amount, date, beneficiary, match_status

### View: Cheque Detail

**URL**: `/dashboard/cheque/<cheque_id>/`
**Returns**:
- cheque data with OCR fields and status indicators
- images (front, back, UV)
- chronology (status history)

### Admin Interface

**URL**: `/admin/`
- Full CRUD operations on all models
- Color-coded status badges
- Advanced filtering and search
- Audit log viewing

---

## 📚 Next Steps

1. ✅ PostgreSQL database created
2. ✅ Django models defined
3. ✅ Migrations applied
4. ✅ Sample data loaded
5. ⏭️ Connect scanner image upload functionality
6. ⏭️ Integrate OCR machine API
7. ⏭️ Build approval workflow UI
8. ⏭️ Add export/reporting features

---

## 💡 Tips

- **Backup database**: `pg_dump -U postgres cheque_system_db > backup.sql`
- **Restore database**: `psql -U postgres -d cheque_system_db < backup.sql`
- **View all users**: `psql -U postgres -l`
- **Drop database**: `dropdb -U postgres cheque_system_db`
- **Admin interface is your friend** - Use it to verify data!

---

For detailed information, see [DATABASE_SETUP.md](DATABASE_SETUP.md)
