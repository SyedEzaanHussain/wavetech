# AZIMUT LABS Cheque System Setup

This repository contains the AZIMUT LABS cheque processing dashboard built with Django.

## Prerequisites

- Python 3.10+
- PostgreSQL 12+ (recommended)
- pip

## 1. Install dependencies

Open a terminal in the repository root:

```bash
cd d:\ChequeSystemProject\ChequeSystem
pip install -r requirements.txt
```

## 2. Configure the database

Update `config/settings.py` if your database settings differ.

For local PostgreSQL, the default connection should use:

- database: `cheque_system_db`
- user: `postgres`
- password: `postgres`
- host: `127.0.0.1`
- port: `5432`

If using SQLite for a quick local test, no additional database setup is required.

## 3. Apply migrations

```bash
python manage.py migrate
```

## 4. Load sample data (optional)

```bash
python manage.py load_sample_data
```

## 5. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

## 6. Run the development server

```bash
python manage.py runserver
```

Open the app at:

- `http://127.0.0.1:8000/dashboard/`
- `http://127.0.0.1:8000/dashboard/queue/`
- `http://127.0.0.1:8000/admin/`

## Notes

- `requirements.txt` contains the required Python packages.
- `setup.bat` and `setup.sh` are quick setup helpers for Windows and Unix.
- Use the dashboard search box to find cheques by tracking number, payee, cheque number, or account number.
