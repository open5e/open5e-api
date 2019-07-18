FROM python:3.7

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api
# copy our project code

# install our dependencies
RUN pip install pipenv gunicorn
COPY . /opt/services/open5e-api

RUN pipenv install

# migrate the db
RUN pipenv run python manage.py migrate

# collect the static files
RUN pipenv run python manage.py collectstatic --noinput

#populate the db
RUN pipenv run python manage.py populatedb --flush ./data/WOTC_5e_SRD_v5.1/

#build the search index
RUN pipenv run python manage.py update_index --remove

# Create the self-signed certs for gunicorn.
RUN pipenv run sh ./scripts/generate_self_signed_cert.sh

#run gunicorn.
CMD ["pipenv", "run", "gunicorn","--certfile=${CERTFILE}", "--keyfile=${KEYFILE}","-b", ":8888", "server.wsgi:application"]