# PostgreSQL Database Setup Guide

This guide helps you set up the PostgreSQL database for the ChequeDB system.

## Prerequisites

- PostgreSQL 12+ installed on your system
- pgAdmin (optional, but helpful for GUI management)
- Python environment configured in the project

## Step 1: Create PostgreSQL Database and User

### Option A: Using PostgreSQL Command Line (psql)

```bash
# Open PostgreSQL command prompt
psql -U postgres

# Create database
CREATE DATABASE cheque_system_db;

# Create user (if not exists)
CREATE USER postgres WITH PASSWORD 'postgres';

# Grant privileges
ALTER ROLE postgres SET client_encoding TO 'utf8';
ALTER ROLE postgres SET default_transaction_isolation TO 'read committed';
ALTER ROLE postgres SET default_transaction_deferrable TO on;
ALTER ROLE postgres SET default_transaction_level TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE cheque_system_db TO postgres;

# Enable UUID extension
\c cheque_system_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Exit psql
\q
```

### Option B: Using pgAdmin GUI

1. Open pgAdmin
2. Right-click on "Databases" → "Create" → "Database"
3. Name: `cheque_system_db`
4. Owner: `postgres`
5. Click "Save"
6. Select the database and go to "Query Tool"
7. Execute: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`

## Step 2: Verify PostgreSQL Connection

Edit `config/settings.py` and verify database configuration:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "s4FMZrQYLlfNpaIs",
        "HOST": "db.jeivqusyirujrchbrabq.supabase.co",
        "PORT": "5432",
    }
}
```

**Note:** Change username/password if you used different credentials.

## Step 3: Run Migrations

From the project directory:

```bash
# Apply all migrations
python manage.py migrate

# Apply dashboard app migrations specifically
python manage.py migrate dashboard
```

Expected output:
```
Running migrations:
  Applying dashboard.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying contenttypes.0001_initial... OK
  ... (other migrations)
```

## Step 4: Load Sample Data (Optional)

```bash
python manage.py shell
```

Then in the Python shell:

```python
from dashboard.models import Cheque, ChequeImage, OCRData
from decimal import Decimal
from datetime import date

# Create a sample cheque
cheque = Cheque.objects.create(
    tracking_no='CHQ-10482',
    cheque_no='10482',
    account_no='1234567890',
    bank_code='HBLC',
    branch_code='001',
    amount=Decimal('1268.69'),
    amount_in_words='ONE THOUSAND TWO HUNDRED SIXTY-EIGHT AND 69/100',
    beneficiary_name='JANIE GOULD',
    cheque_date=date(2026, 6, 9),
    status='pending',
    match_status='mismatch'
)

# Create OCR data
OCRData.objects.create(
    cheque=cheque,
    field_name='amount',
    field_value='1268.69',
    confidence_score=85.5
)

OCRData.objects.create(
    cheque=cheque,
    field_name='date',
    field_value='6/9/2026',
    confidence_score=92.3
)

OCRData.objects.create(
    cheque=cheque,
    field_name='beneficiary_name',
    field_value='JANIE GOULD',
    confidence_score=78.2
)

OCRData.objects.create(
    cheque=cheque,
    field_name='amount_in_words',
    field_value='THOUSAND NINE HUNDRED FIFTY AND 00/100',
    confidence_score=65.8
)

# Exit shell
exit()
```

## Step 5: Create Django Admin Superuser

```bash
python manage.py createsuperuser
```

Follow prompts to create admin account.

## Step 6: Run the Server

```bash
python manage.py runserver
```

Access the application:
- Dashboard: http://127.0.0.1:8000/dashboard/
- Queue: http://127.0.0.1:8000/dashboard/queue/
- Admin: http://127.0.0.1:8000/admin/

## Database Structure

### Tables Created

| Table | Purpose |
|-------|---------|
| `cheques` | Main cheque documents |
| `cheque_images` | Cheque image files (front, back, UV) |
| `ocr_data` | OCR extracted field data |
| `processing_queue` | Cheques pending processing |
| `status_history` | Audit trail of status changes |
| `audit_log` | Complete audit log of all changes |
| `users` | User accounts and roles |

### Data Flow

```
Scanner → Cheques Table ← OCR Machine
   ↓
ChequeImages (Front/Back/UV)
   ↓
OCRData (Extracted fields)
   ↓
ProcessingQueue (Workflow)
   ↓
StatusHistory (Audit trail)
   ↓
AuditLog (Complete history)
```

## Troubleshooting

### "password authentication failed for user 'postgres'"
- Verify PostgreSQL is running: `pg_isready -h localhost`
- Check username and password in settings.py
- Reset PostgreSQL password:
  ```bash
  # Windows: Use Services to start PostgreSQL
  # Then in psql: ALTER USER postgres PASSWORD 'newpassword';
  ```

### "database 'cheque_system_db' does not exist"
- Create database following Step 1 above
- Verify database name matches in settings.py

### "psycopg2 installation failed"
- Windows: Install via: `pip install psycopg2-binary`
- Linux: Install system dependency: `sudo apt-get install postgresql-client`
- macOS: `brew install postgresql`

### UUID extension not available
- Connect to database and run:
  ```sql
  CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  ```

## Next Steps

1. ✅ Database is set up
2. ✅ Migrations are applied
3. ✅ Sample data is loaded
4. Navigate to http://127.0.0.1:8000/dashboard/queue/ to see cheques
5. Click eye icon to view cheque details with OCR data
6. Click Approve/Reject to update status (tracked in status_history)
7. All actions are logged in audit_log

## Backup and Recovery

### Backup database
```bash
pg_dump -U postgres cheque_system_db > backup.sql
```

### Restore database
```bash
psql -U postgres -d cheque_system_db < backup.sql
```
