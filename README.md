<p align="center">
  <img src="static/logo.png" width="200px" align="center" alt="Open5e logo" />
  <h1 align="center">Open5e API</h1>
  <p align="center">
    <a href="https://open5e.com">https://open5e.com</a>
    <br/>
    A JSON API for the D&D 5e gamesystem
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

# Table of contents

- [Table of contents](#table-of-contents)
- [Introduction](#introduction)
- [Installation](#installation)
  * [Requirements](#requirements)
  * [Modules](#modules)
- [Development](#development)
  * [Build](#build)
    + [Search Indexing](#search-indexing)
  * [Run](#run)
  * [Building the OAS file](#building-the-oas-file)
- [Contributing](#contributing)
  * [Editing existing sources](#editing-existing-sources)
  * [Adding a new source](#adding-a-new-source)
  * [Change existing models](#change-existing-models)
- [Tests](#tests)
- [Deployment](#deployment)
  * [DigitalOcean](#digitalocean)
  * [Railway.app](#railwayapp)
  * [Docker](#docker)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>

# Introduction

Open5e is a community project driven by a small number of volunteers in their spare time. We welcome any and all contributions! Please join our Discord to help out: https://discord.gg/9RNE2rY or check out the issue board if you'd like to see what's being worked on!

The API uses the Django REST Framework for it's browsability and ease of use when developing CRUD endpoints. It uses django's default SQLite database, and pulls the data from the `/data` directory.

# Installation

## Requirements

- [Python 3.11](https://www.python.org/downloads/)

- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)

## Dependencies

Pipenv is used to install all required packages from the `Pipfile` at the project root. Use the following command after cloning the project or switching branches.

```bash
pipenv install --dev
```

# Development

## Build

Create a local database, import game content, and set up search indexes:

```bash
pipenv run python manage.py quicksetup
```

Run this again if you switch git branches or pull new changes.


### Search Indexing

Search indexes are pre-built and included in the repo. Running `quicksetup` unpacks them automatically:

```bash
pipenv run python manage.py quicksetup
```

If you've changed data in `data/`, rebuild the indexes before committing:

```bash
pipenv run python manage.py quickindex
```

This takes 2-3 minutes and updates `search/indexes/` which should be committed with your data changes.

## Run

Run the server locally. This server is only for development and shall __not__ be used in production. The server will be available at `http://localhost:8000`.

```bash
pipenv run python manage.py runserver
```

### Self-hosting
If you would like to host the API yourself locally, we suggest using gunicorn as your wsgi server. Below is an equivalent command to what we use in production, which makes the server available at `http://localhost:8888`.

```bash
gunicorn -b :8888 server.wsgi:application
```

You can use our Dockerfile as inspiration, but it likely will not work without significant edits to your operating environment. We have customized our production environment to use it.

## Building the OAS file

After completing a build, you can generate an OAS file to be used by another application.
```bash
pipenv run python manage.py spectacular --color --file openapi-schema.yml` to build the OAS file.
```

# Contributing

We welcome contributions! Please join our [Discord](https://discord.gg/9RNE2rY) to coordinate with the team, or check out the [issue board](https://github.com/open5e/open5e-api/issues) to see what's being worked on.
# Tests

Tests are located in `api/tests` and `api_v2/tests`. Run them before pushing new changes. Tests require the API to be [running](##run) at `http://localhost:8000`.

```bash
pipenv run pytest
```

## Approval tests
Approval tests compare API responses against pre-approved JSON files in `api_v2/tests/responses/*.approved.json`. If a test fails, the received response is saved as `*.received.json`. To approve changes, rename the received file to replace the approved file.

Received files should not be committed to git.


# Deployment

## DigitalOcean

This deployment has been tested using [DigitalOcean Apps](https://www.digitalocean.com/go/cloud-hosting) with Docker Hub.

To start up the server from scratch on a droplet:

```bash
git pull https://github.com/open5e/open5e-api
export SECRET_KEY=a_new_secret_key
export SERVER_NAME=whatever.yourdomain.com
cd open5e-api/
docker-compose up
```

## Railway.app
1. Create a fork on Github. This is used to automatically deploy whenever you make a change.
2. Login with your Github account on [Railway.app](https://railway.app) and give it access to manage your forked repository.
3. Create a new Project and choose 'Deploy from GitHub repo'. Select your fork in the list.
4. Keep all settings default and deploy. Accept when Railway asks to copy variables existing variables from the repository.
5. Add the variable `PORT` with the value `8888`.
6. Add the variable `SERVER_NAME` with the [Railway-provided domain](https://docs.railway.app/deploy/exposing-your-app#railway-provided-domain) or add your own. 
7. Push a commit to Github and watch your open5e-api redeploy in minutes!


## Docker

With docker installed, you can build the project with provided Dockerfile

```bash
docker build
```

This docker app can then be deployed with any provider.
