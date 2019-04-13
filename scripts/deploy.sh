#!/bin/bash

# Author: augustjohnson on 2018.08.12.  

#Pulling source code and dependencies using pipenv. 
pipenv install -r

echo "[OPEN5E DEPLOYER] Checking out new code, but keeping localized edits (to settings.py for example)."
# Stash existing, locally edited files.
git stash
# git pull
git pull
# pop the stash.
git stash pop

echo "[OPEN5E DEPLOYER] Running standard django deployment steps, migrate and collectstatic."
# django makemigrations

pipenv run python manage.py makemigrations
pipenv run python manage.py migrate
pipenv run python manage.py populatedb --flush ./data/WOTC_5e_SRD_v5.1/
pipenv run python manage.py collectstatic

echo "[OPEN5E DEPLOYER] Reloading config, and restarting webservices."
# Reload config and start services that were stopped.
pipenv run python manage.py runserver