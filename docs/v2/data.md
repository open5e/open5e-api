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





