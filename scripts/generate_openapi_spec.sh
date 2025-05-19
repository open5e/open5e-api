# This script takes the code repo as the input and generates an openapi spec as the output.
# Parameters:
# Version takes in a string that will be shown in the API docs.
pip install pipenv
pipenv install
pipenv run python manage.py spectacular --color --file schema.yml --validate --fail-on-warn 