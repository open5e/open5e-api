## Export
To export data, there's a new django command. All models in both v1 and v2 are supported for export, although at this time only v2 models could be edited while the site was live.

```shell
pipenv run python manage.py export --dir data
```

This is based on logic found [here](../../api_v2/management/commands/export.py), and leverages django's built-in concept of fixtures, but structures the 
folders in a way that's consistent and flexible.

## Known Issues
- When exporting the data, some `v1` resources are slightly changed because of timestamp fields being updated the last time quicksetup was run. Make sure to roll these changes back before committing.