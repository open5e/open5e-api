## Export
To export data, there's a new django command. For now only models used in the v2 API are supported for export.
```shell
pipenv run python manage.py export --dir data
```

This is based on logic found [here](../../api_v2/management/commands/export.py), and leverages django's built-in concept of fixtures, but structures the 
folders in a way that's consistent and flexible.

## Known Issues
- When exporting the data, some `v1` resources are slightly changed. Make sure to roll these changes back before committing.