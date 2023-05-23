![API status](https://img.shields.io/website?down_message=Down&label=Open5e%20API&up_message=Up&url=https%3A%2F%2Fapi.open5e.com)

Open5e is a community project driven by a small number of volunteers in their spare time. We welcome any and all contributions! Please join our Discord to help out: https://discord.gg/9RNE2rY or check out the issue board if you'd like to see what's being worked on!

The Django API uses Django REST Framework for its browsability and ease of use when developing CRUD endpoints.  It uses django's default SQLite database, and pulls the data from the /data directory.

# Install Prerequisites

1.  Install the sqlite3 development package. On Ubuntu, the package is called
    `sqlite3-devel`. On Debian-based systems, it's called `libsqlite3-dev`.

1.  This project currently uses python3.8 configured with loadable sqlite
    extensions. If you don't have python3.8, or if you aren't sure that your
    python3.8 installation has loadable sqlite extensions enabled, download and
    install the python3.8 source
    [here](https://www.python.org/downloads/release/python-3816/). Installation
    instructions are in the README found in the source tarball. When you
    configure it, be sure to to use
    `./configure --enable-loadable-sqlite-extensions`.

1.  We use pipenv to manage our Python dependencies. Installation instructions
    are on the [pipenv website](https://pipenv.readthedocs.io/en/latest/).

1.  Once pipenv is installed, you can install all of the project dependencies
    defined in the Pipfile via `pipenv install --dev`.

## Quick Setup

To do any python development on the django application itself, I would suggest using django's built-in server as it allows for various things (such as debug mode and quick reloads).  Here's the general process for getting that up and running.

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

## Tests

### To run the test suite:

First, install the prerequisites as described above

Then, install dev requirements:

```
pipenv install --dev
```

Then, run the test suite:
```
pipenv run pytest
```

## Starting up a droplet

This deployment has been tested using DigitalOcean Apps with Docker Hub.

To start up the server from scratch on a droplet:

```
git pull https://github.com/open5e/open5e-api
export SECRET_KEY=a_new_secret_key
export SERVER_NAME=whatever.yourdomain.com
cd open5e-api/
docker-compose up
```

## Deploying on Railway.app
1. Create a fork on Github.com This is used to automatically deploy when you make a change.
2. Login with your Github account on [Railway.app](https://railway.app) and give it access to manage your forked repository.
3. Create a new Project and choose 'Deploy from GitHub repo'. Select your fork in the list.
4. Keep all settings default and deploy. Accept when Railway asks to copy variables existing variables from the repository.
5. Add the variable `PORT` with the value `8888`.
6. Add the variable `SERVER_NAME` with the [Railway-provided domain](https://docs.railway.app/deploy/exposing-your-app#railway-provided-domain) or add your own. 
7. Push a commit to Github and watch your open5e-api redeploy in minutes!

## Building the OAS file

Once you have everything set up, run `pipenv run ./manage.py generateschema --generator_class api.schema_generator.Open5eSchemaGenerator > openapi-schema.yml` to build the OAS file.
