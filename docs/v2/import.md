## Import
To import data, there's a new django command.
```shell
pipenv run python manage.py import --dir data
```
This is based on logic found [here](../../api_v2/management/commands/import.py), 
and leverages django's built-in concept of fixtures.

This import command only imports all fixtures in the data directory. It has been added as part of `quicksetup` 
command (see [README.md](../../README.md)).

