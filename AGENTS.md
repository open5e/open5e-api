This is a project that encodes 5th Edition Dungeons and Dragons rules into an API.

To ingest data, it is best to run `manage.py quicksetup` from within the pipenv environment. You can check the readme.md for additional instructions about using this repo.

Before calling a task finished, always run scripts like `quicksetup` and tests, plus any other reasonable checks, to ensure that data can correctly be ingested and your changes work.

All data is populated by ingesting .json files from the /data/v1 or /data/v2 directory using Django fixtures, it does not have a persistent database.

The current main project on this repo is converting data from the v1 format to the much more structured v2 format. This requires a lot of interpretation and parsing of old data, and the new endpoints for v2 are still being developed. Where possible, we want to create re-runnable scripts and use them to populate the new structure, but it may be more efficient for you to simply parse the data re-write it yourself, so to speak.

There is also an ongoing project to convert new unstructured pdf text material into the structured v2 format. This is due to new material being published. Each PDF tends to be unique so must be handled differently.
