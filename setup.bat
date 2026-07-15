@echo off
REM Quick Start Guide for ChequeDB (Windows)

echo ================================
echo ChequeDB - Quick Start Setup
echo ================================
echo.

echo 📦 Step 1: Installing dependencies...
pip install -r requirements.txt

echo.
echo 🗄️  Step 2: Running database migrations...
python manage.py migrate

echo.
echo ✅ Setup Complete!
echo.
echo To start the development server, run:
echo   python manage.py runserver 8000
echo.
echo Then open your browser and navigate to:
echo   http://127.0.0.1:8000/dashboard/
echo.
echo To create an admin user, run:
echo   python manage.py createsuperuser
echo.
echo Access admin panel at:
echo   http://127.0.0.1:8000/admin/
echo.
pause
