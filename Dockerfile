FROM python:3.11-slim

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api
# copy our project code

# install our dependencies
RUN pip install pipenv gunicorn
COPY . /opt/services/open5e-api

# assert that debug is off to avoid errors due to missing dev dependencies
ENV OPEN5E_DEBUG=False

RUN pipenv install

# migrate the db, load content, and index it
RUN pipenv run python manage.py quicksetup

# remove .env file (set your env vars via docker-compose.yml or your hosting provider)
RUN rm .env

#run gunicorn.
CMD ["pipenv", "run", "gunicorn","-b", ":8888", "server.wsgi:application"]