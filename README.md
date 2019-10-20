# open5e is being rebuilt in Django and Vue.js!

Open5e is a community project driven by a small number of volunteers in their spare time. We welcome any and all contributions! Please join our Discord to help out: https://discord.gg/9RNE2rY or check out the issue board if you'd like to see what's being worked on!

The Django API uses Django REST Framework for its browsability and ease of use when developing CRUD endpoints.  It uses django's default SQLite database, and pulls the data from the /data directory.

# Development using Django Server
To do any python development on the django application itself, I would suggest using django's built-in server as it allows for various things (such as debug mode and quick reloads).  Here's the general process for getting that up and running.

First, install pipenv from here (https://pipenv.readthedocs.io/en/latest/). 

Once pipenv is installed locally, you can then use it to install of the project dependencies defined in the Pipfile.
> pipenv install

## Quick Setup
If you want to work with existing data sources and just get working you can quickly stand up the server with

> pipenv run python manage.py quicksetup

followed by

> pipenv run python manage.py runserver

This will stand up the server with full content and search index at http://localhost:8000.

## Manual Setup Steps
If you want to customize your setup, particularly useful if adding new content sources, then you will need to use the built-in django migration function to define your database, making sure to run it within the pipenv environment.
> pipenv run python manage.py migrate

You will then need to collect the static files (this makes django-resk-framework look presentable when viewing it in html).
> pipenv run python manage.py collectstatic --noinput

Finally, you will need to load the SRD data from the json files in the /data folder.  This is using the custom populatedb command.
> pipenv run python manage.py populatedb --flush ./data/WOTC_5e_SRD_v5.1/

At that point, you will be able to run the django server normally (within the pipenv environment).
> pipenv run python manage.py runserver

And your server should be available at http://localhost:8000.
