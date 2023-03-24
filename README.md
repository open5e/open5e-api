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
    defined in the Pipfile via `pipenv install`.

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

## Starting up a droplet

This deployment has been tested using DigitalOcean with Docker.

To start up the server from scratch on a droplet:

```
git pull https://github.com/open5e/open5e-api
export SECRET_KEY=a_new_secret_key
export SERVER_NAME=whatever.yourdomain.com
cd open5e-api/
docker-compose up
```

## Building the OAS file

Once you have everything set up, you should be able to run `pipenv run ./manage.py generateschema --generator_class api.schema_generator.Open5eSchemaGenerator > openapi-schema.yml` and regenerate the OAS file.