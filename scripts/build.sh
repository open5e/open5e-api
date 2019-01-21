
heroku config:unset PYTHONHOME
pipenv run pip install -r ./requirements.txt
pipenv run python manage.py migrate
pipenv run python manage.py populatedb --flush ./data/WOTC_5e_SRD_v5.1/
pipenv run python --version