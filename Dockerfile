FROM python:3.11-alpine

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api
# copy our project code

# install our dependencies
RUN pip install pipenv gunicorn
COPY . /opt/services/open5e-api

RUN pipenv install

RUN cd /proc/sys/kernel && mkdir /tmp/proc && mount -t procfs none /tmp/proc && mount -t tmpfs none ./random && cd random && ln -s /tmp/proc/sys/kernel/random/uuid uuid && ln -s /tmp/proc/sys/kernel/random/poolsize poolsize && ln -s /tmp/proc/sys/kernel/random/entropy_avail entropy_avail && echo 60287c01-cb1b-4faa-b99c-f6ae4b14d9b6 >> boot_id && cat /proc/sys/kernel/random/boot_id

# migrate the db, load content, and index it
RUN pipenv run python manage.py quicksetup

# remove .env file (set your env vars via docker-compose.yml or your hosting provider)
RUN rm .env

#run gunicorn.
CMD ["pipenv", "run", "gunicorn","-b", ":8888", "server.wsgi:application"]
