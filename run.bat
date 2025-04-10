@echo off
echo Starting Git Pull and Django Server...

:: Change to your project directory - replace with your actual path
cd /d C:\BackendDAM\BackendDAM

:: Activate virtual environment
call venv\Scripts\activate

:: Pull latest changes from Git
echo Pulling latest changes from Git...
git pull

:: Set name user pass
set DB_NAME=DB-DAM
set DB_USER=sa
set DB_PASSWORD=Bc@f2020++
set DB_HOST=192.168.1.21
set DB_PORT=8000

:: Run migrations
echo Running migrations...
python manage.py migrate

:: Collect static files (uncomment if needed)
:: echo Collecting static files...
:: python manage.py collectstatic --noinput

:: Start Django server
echo Starting Django development server...
python manage.py runserver 0.0.0.0:8000

:: Note: This will keep running until you press Ctrl+C