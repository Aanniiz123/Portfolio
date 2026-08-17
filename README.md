This is my Portfolio and

## Creating the virtual enviroment
python -m venv venv

## Deactiving the virtual enviroment

.\venv\Scripts\Activate.ps1   (Power shell)
venv\Scripts\activate.bat  (Command prompt)

### Requriment File 
pip install -r requirements.txt

## to run the project 
1. python manage.py loaddata fixtures.json
2. python manage.py makemigration
3. python manage.py migrate

4. python manage.py runserver