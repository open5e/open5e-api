FROM python:3.11-alpine

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api
# copy our project code

# install our dependencies
RUN pip install pipenv gunicorn
COPY . /opt/services/open5e-api

RUN pipenv install

RUN cd /proc/sys/kernel && sudo mkdir /tmp/proc && sudo mount -t procfs none /tmp/proc && sudo mount -t tmpfs none ./random && cd random && sudo ln -s /tmp/proc/sys/kernel/random/uuid uuid && sudo ln -s /tmp/proc/sys/kernel/random/poolsize poolsize && sudo ln -s /tmp/proc/sys/kernel/random/entropy_avail entropy_avail && sudo echo 60287c01-cb1b-4faa-b99c-f6ae4b14d9b6 >> boot_id && cat /proc/sys/kernel/random/boot_id

# migrate the db, load content, and index it
RUN pipenv run python manage.py quicksetup

# remove .env file (set your env vars via docker-compose.yml or your hosting provider)
RUN rm .env

#run gunicorn.
CMD ["pipenv", "run", "gunicorn","-b", ":8888", "server.wsgi:application"]
