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

## Keys
Documents when onboarded are given a short key. To allow for data to be presented in the same views, even with conflicting data names, we by convention choose the keys of an individual data item to be <slugified-name>-<document-pk>, which should be unique in all cases.

**Examples:**
> magic-missile-srd - The original Magic Missile, from Wizard's of the Coast's Systems Reference Document (srd)
>
> acolyte-a5e-ag - The Acolyte Background, from Advanced 5e's Adventurer's Guide (a5e-ag).
