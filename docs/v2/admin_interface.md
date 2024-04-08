# Admin Interface
V2 data can be edited using the built-in django admin interface. This allows for a UI rather than a text-editable field. It works cleanly with import and export below. It is disabled on production and staging, so editing must occur when running the application locally.

## Setup
After installing the project, you will need to create a superuser for the local instance. 
This will allow you to log in and edit the data.

This will force a prompt to create a custom superuser for the local instance. Set any username and password you like you will
only use this once and it is only for your local instance. Just do something simple like `admin` and `admin`.
````shell
pipenv run python manage.py createsuperuser
````
Once done, you should be able to run the server locally.
```shell
pipenv run python manage.py runserver
```
Then you can aim your browser at the default admin interface, and log in using the credentials you just created.
> http://localhost:8000/admin/

You will see the list of the resource types that can be edited. Click on the type you wish to edit to open the full list
of all instances of this resource type. There you can add a new entity or edit an existing one. Fill out the form with 
all required fields and then save. These edits will apply to only your local database. Use the
[export command](./export.md) to save your changes to the source files. Then make your commit and push your changes.

Make sure to review the changes after the export to ensure that the data is correct and you made no unintended changes.
