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

# Announcement: API V2 has officially launched, and V1 is now in  maintenance. Calls now require a server prefix

If you are using the old V1 API, you will need to prefix your calls with /v1/ (eg. api.open5e.com/v1/monsters). This should resolve issues for anyone currently consuming v1 API and having issues with their site.

This has come after many months of dicussion within our discord and on this repo (and the inclusion of a 299 deprecation warning in every response header). Unfortunately, since we do not require registration for API keys, we have no way to contact consumers other than to update and hope folks find their way here when things break.

The v1 API is now in maintenance, and will not recieve content or functionality updates. We recommend migrating to v2, but will keep the v1 running for as long as it doesn't consume too much resources to do so.

All v1 content is still available for hosting your own version, if required

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
  * [OpenAPI Spec](#openapi-spec)
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
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Dependencies

uv is used to manage dependencies and run commands. Install all dependencies after cloning the project or switching branches:

```bash
uv sync
```

# Development

## Build

Create a local database and import game content.
```bash
uv run python manage.py quicksetup --noindex
```

To make sure the API is always using your updated code, this command must be run again if:
- You add/remove/edit Game Content
- You edit Python code
- You switch git branches


### Search Indexing

To use the search function, you must build the search index by running the above command without the `--noindex` flag.
```bash
uv run python manage.py quicksetup
```

## Run

Run the server locally. This server is only for development and shall __not__ be used in production. The server will be available at `http://localhost:8000`.

```bash
uv run python manage.py runserver
```

### Self-hosting
If you would like to host the API yourself locally, we suggest using gunicorn as your wsgi server. Below is an equivalent command to what we use in production, which makes the server available at `http://localhost:8888`.

```bash
gunicorn -b :8888 server.wsgi:application
```

You can use our Dockerfile as inspiration, but it likely will not work without significant edits to your operating environment. We have customized our production environment to use it.

## OpenAPI Spec

`openapi-schema.yml` (at the repo root) is the canonical API contract for `/v2/`,
generated from the serializers/views by drf-spectacular. It is committed to the
repo so consumers and reviewers can read and diff the contract directly.

CI verifies it stays in sync with the code on every PR into `staging-with-spec`.
If you change a serializer, view, model, or schema-affecting setting, regenerate:

```bash
uv run python manage.py spectacular --file openapi-schema.yml
```

Then commit the updated file. Do **not** hand-edit `openapi-schema.yml` — it is
a build artifact.

# Contributing
See [contribution guide](.github/CONTRIBUTING.md).
# Tests

Tests are located in the `api/tests` directory. These should be run before pushing new changes to the main repository.

```bash
uv run pytest
```

## Approval tests
Approval tests are run against the approved files in `api/tests/approved_files` as `*.approved.*` . If a test fails then the recieved input will be stored in a `*.recieved.*` file. If you wish to approve the changes, replace the old approved file with the recieved file.

Recieved files shall not be included in the git repo.

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
