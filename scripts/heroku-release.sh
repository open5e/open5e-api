
pip install -r requirements.txt

python ../manage.py makemigrations
# django migrate
python ../manage.py migrate
# django collectstatic
python ../manage.py collectstatic
