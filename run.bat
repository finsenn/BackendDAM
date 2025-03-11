@echo off
echo Starting Git Pull and Django Server...

:: Change to your project directory - replace with your actual path
cd /d C:\BackendDAM\BackendDAM

:: Activate virtual environment
call venv\Scripts\activate

:: Pull latest changes from Git
echo Pulling latest changes from Git...
git pull

:: Install or update dependencies
echo Updating dependencies...
pip install -r requirements.txt

:: Run migrations
echo Running migrations...
python manage.py migrate

:: Collect static files (uncomment if needed)
:: echo Collecting static files...
:: python manage.py collectstatic --noinput

:: Start Django server
echo Starting Django development server...
python manage.py runserver

:: Note: This will keep running until you press Ctrl+C