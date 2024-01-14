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

- [Pipenv](https://pipenv.pypa.io/en/latest/installation/)

## Modules

Pipenv is used to install all required packages from the `Pipfile` at the project root. Use the following command after cloning the project or switching branches.

```bash
pipenv install --dev
```

# Development

## Build

Crate a local database and import game content. 
```bash
pipenv run python manage.py quicksetup --noindex
```

To make sure the API is always using your updated code, this command must be run again if:
- You add/remove/edit Game Content
- You edit Python code
- You switch git branches


### Search Indexing

To use the search function, you must build the search index by running the above command without the `--noindex` flag.
```bash
pipenv run python manage.py quicksetup
```


## Run

Run the server locally. This server is only for development and shall __not__ be used in production. The server will be available at `http://localhost:8000`.

```bash
pipenv run python manage.py runserver
```

If you need to run the server on another port, add the port number as an argument.

```bash
pipenv run python manage.py runserver $PORT
```


## Building the OAS file

After completing a build, you can generate an OAS file to be used by another application.
```bash
pipenv run ./manage.py generateschema --generator_class api.schema_generator.Open5eSchemaGenerator > openapi-schema.yml` to build the OAS file.
```

# Contributing

Before making any changes, you should fork the Ope5e-api repository. This will make a copy on your account, which can be freely edited. Once your edits are done you can open a Pull Request to have your changes reviewed by a maintainer, which may ask for changes or clarification before approving it. Once merged the changes go live on [Beta Site](https://beta.open5e.com) before being pushed live.

Smaller edits such as spelling mistakes can be edited directly in Github. For larger edits, it is recommeded that you make changes in a full editor, such as [VS Code](https://code.visualstudio.com) with the [Github Extenstion](https://code.visualstudio.com/docs/sourcecontrol/github).

## Editing existing sources

Game Content is stored in the `data` directory. It is first split according `v1` and `v2`, which are distinct API versions. As of 2023-12-06, `v1` is the dataset exclusively used in production, but it's a good idea to check for the same data inside of v2. We use [fixtures](https://docs.djangoproject.com/en/4.2/topics/db/fixtures/) as our primary way of populating the database because of strong built-in support. Each fixture in v1 has been split out by Document Slug, and then Model. Find the one you'd like to edit inside of the appropriate ModelName.json file.

## Adding a new source

To add a new source, create new directory inside `data/v1` and a `Document.json` file that credits the source and links to the license it was published under. An example of this can be found [here](/data/v1/wotc-srd/Document.json). You can then add a json file for each Model Fixture of content. See an existing source, such as the 5.1 SRD to see how these should be structured.

A PK (or Primay Key) is text based slug for all game content, and it's used in the URL for getting that item. In the majority of cases, the PK should be the slugified version of the name. In the cases where an object PK would conflict with an existing PK, prepend a clear identifier to the PK.

**TODO SET CONVENTIONS FOR WHAT THE IDENTIFIER IS**

## Change existing models

Models such as Monsters and Classes are stored in the [api/models](/api/models) directory. These define fields (hp, str, speed) and how they are output. The import of Game Content from `data` is handled by django's built-in [loaddata](https://docs.djangoproject.com/en/4.2/ref/django-admin/#django-admin-loaddata).

# Tests

Tests are located in the `api/tests` directory. These should be run before pushing new changes to the main repository. These tests require that the api is [running](##run) at `http://localhost:8000`.

```bash
pipenv run pytest
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
