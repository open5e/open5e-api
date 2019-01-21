pipenv run pip install requirements.txt
pipenv run python manage.py migrate
pipenv run python manage.py populatedb --flush /data/WOTC_5e_SRD_v5.1/