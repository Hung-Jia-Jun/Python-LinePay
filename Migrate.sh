del /f /s /q db.sqlite3
rmdir /q /s LinepayAPP\\migrations

python3 manage.py makemigrations --empty LinepayAPP
python3 manage.py makemigrations
python3 manage.py migrate