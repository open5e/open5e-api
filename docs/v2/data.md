# Data

Within the v2 api, the data loading is completely distinct from the v1 data. It uses the /data/v2 folder in the repository. It also follows a heirarchy that looks like this:

Descriptions of the licenses for data that we serve, and rulesets for the data.
> /data/v2/License.json
> /data/v2/Ruleset.json

Description of the organization or publishers of the data.
> /data/v2/{publisher-key}/Publisher.json

Description of the document related to the data.
> /data/v2/{publisher-key}/{document-key}/Document.json.

The actual data.
> /data/v2/{publisher-key}/{document-key}/{model-name}.json.

## Import
To import data, there's a new django command.
> python manage.py import --dir data/v2/

This is based on logic found here, and leverages django's built-in concept of fixtures.
> /api_v2/management/commands/import.py


## Admin Interface
V2 data can be edited using the built-in django admin interface. This allows for a UI rather than a text-editable field. It works cleanly with import and export below. It is disabled on production and staging, so editing must occur when running the application locally.

### Setup
To setup the admin interface, first, follow the setup instructions in Readme.md. Then try the following commands.

This will force a prompt to create a custom superuser for the local instance.
> python manage.py createsuperuser

Once done, you should be able to run the server.
> python manage.py runserver

Then you can aim your browser at the default admin interface, and log in using the credentials you just created.
> http://localhost:8000/admin/

You will see forms and lists of objects that are editable. These edits will apply to only your local database.

## Export
To export data, there's a new django command. For now only models used in the v2 API are supported for export.
> python manage.py export --dir data/

This is based on logic found here, and leverages django's built-in concept of fixtures, but structures the folders in a way that's consistent and flexible.
> /api_v2/management/commands/export.py
