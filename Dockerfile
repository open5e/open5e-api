FROM python:3.8

RUN mkdir -p /opt/services/open5e-api
WORKDIR /opt/services/open5e-api
# copy our project code

# install our dependencies
RUN pip install pipenv gunicorn
COPY . /opt/services/open5e-api

RUN pipenv install

# migrate the db
RUN pipenv run python manage.py makemigrations
RUN pipenv run python manage.py migrate

# collect the static files
RUN pipenv run python manage.py collectstatic --noinput

#add original open5e content
RUN pipenv run python manage.py populatedb --flush ./data/open5e_original/

#populate the db
RUN pipenv run python manage.py populatedb --append ./data/WOTC_5e_SRD_v5.1/

#add the tome of beasts
RUN pipenv run python manage.py populatedb --append ./data/tome_of_beasts/

#add the creature codex
RUN pipenv run python manage.py populatedb --append ./data/creature_codex/

#add the tome of beasts 2
RUN pipenv run python manage.py populatedb --append ./data/tome_of_beasts_2/

#add deep magic
RUN pipenv run python manage.py populatedb --append ./data/deep_magic/

#add deep magic
RUN pipenv run python manage.py populatedb --append ./data/tome_of_beasts_3/

#add monstrous menegerie
RUN pipenv run python manage.py populatedb --append ./data/menagerie/

#build the search index
RUN pipenv run python manage.py update_index --remove

# Create the self-signed certs for gunicorn.
RUN pipenv run sh ./scripts/generate_self_signed_cert.sh

#run gunicorn.
CMD ["pipenv", "run", "gunicorn","--certfile=${CERTFILE}", "--keyfile=${KEYFILE}","-b", ":8888", "server.wsgi:application"]
