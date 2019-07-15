del /f /s /q D:\pythonScript\LinepayProject\LinePayDjangoServer\Django\Scripts\LinePay\db.sqlite3
rmdir /q /s D:\pythonScript\LinepayProject\LinePayDjangoServer\Django\Scripts\LinePay\LinepayAPP\migrations

python manage.py makemigrations --empty LinepayAPP
python manage.py makemigrations
python manage.py migrate