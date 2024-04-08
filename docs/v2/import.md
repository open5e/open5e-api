## Import
To import data, there's a new django command.
```shell
pipenv run python manage.py import --dir data/v2/
```
This is based on logic found [here](../../api_v2/management/commands/import.py), 
and leverages django's built-in concept of fixtures.

This import command only imports the `v2` data. If you need to import v1 data, use the `quicksetup` 
command (see [README.md](../../README.md)).

