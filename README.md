<p align="center">
  <img src="logo.png" width="200px" align="center" alt="Open5e logo" />
  <h1 align="center">Open5e API</h1>
  <p align="center">
    <a href="https://open5e.com">https://open5e.com</a>
    <br/>
    A JSON API for the D&D 5e ruleset
  </p>
</p>
<br />

<p align="center">
<a href="https://api.open5e.com" rel="nofollow"><img src="https://img.shields.io/website?down_message=Down&label=Open5e%20API&up_message=Up&url=https%3A%2F%2Fapi.open5e.com" alt="API"></a>
<a href="https://open5e.com" rel="nofollow"><img src="https://img.shields.io/website?down_message=Down&label=Open5e&up_message=Up&url=https%3A%2F%2Fopen5e.com" alt="homepage"></a>
</p>

<div align="center">
    <a href="https://api.open5e.com">API</a>
    <span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
    <a href="https://discord.gg/9RNE2rY">Discord</a>
    <span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
    <a href="https://www.patreon.com/open5e">Patreon</a>
</div>

<br/>

Open5e is a community project driven by a small number of volunteers in their spare time. We welcome any and all contributions! Please join our Discord to help out: https://discord.gg/9RNE2rY or check out the issue board if you'd like to see what's being worked on!

The API uses the Django REST Framework for it's browsability and ease of use when developing CRUD endpoints. It uses django's default SQLite database, and pulls the data from the `/data` directory.

# Installation

## Requirements

- [Python 3.11](https://www.python.org/downloads/)

- [Pipenv](https://pipenv.pypa.io/en/latest/installation/)

## Modules

Use pipenv to install all required packages from the `Pipfile` at the project root.

```
pipenv install --dev`
```

## Quick Setup

To do any python development on the django application itself, I would suggest using django's built-in server as it allows for various things (such as debug mode and quick reloads).  Here's the general process for getting that up and running.

If you want to work with existing data sources and just get working you can quickly stand up the server with

```bash
pipenv run python manage.py quicksetup
```

followed by

```bash
pipenv run python manage.py runserver
```

This will stand up the server with full content and search index at http://localhost:8000.

## Manual Setup Steps

If you want to customize your setup, particularly useful if adding new content sources, then you will need to use the built-in django migration function to define your database, making sure to run it within the pipenv environment.

```bash
pipenv run python manage.py migrate
```

You will then need to collect the static files (this makes django-resk-framework look presentable when viewing it in html).

```bash
pipenv run python manage.py collectstatic --noinput
```

Finally, you will need to load the SRD data from the json files in the /data folder.  This is using the custom populatedb command.

```bash
pipenv run python manage.py populatedb --flush ./data/WOTC_5e_SRD_v5.1/
```

At that point, you will be able to run the django server normally (within the pipenv environment).

```bash
pipenv run python manage.py runserver
```

And your server should be available at http://localhost:8000.

## Tests

### To run the test suite:

First, install the prerequisites as described above

Then, install dev requirements:

```bash
pipenv install --dev
```

Then, run the test suite:

```bash
pipenv run pytest
```

## Starting up a droplet

This deployment has been tested using DigitalOcean Apps with Docker Hub.

To start up the server from scratch on a droplet:

```bash
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
