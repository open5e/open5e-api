# Data

Within the v2 api, the data loading is completely distinct from the v1 data. It uses the /data/v2 folder in the repository. It also follows a heirarchy that looks like this:

Descriptions of the licenses for data that we serve, and gamesystems for the data.
> /data/v2/License.json
> /data/v2/GameSystem.json

Description of the organization or publishers of the data.
> /data/v2/{publisher-key}/Publisher.json

Description of the document related to the data.
> /data/v2/{publisher-key}/{document-key}/Document.json.

The actual data.
> /data/v2/{publisher-key}/{document-key}/{model-name}.json.

## Keys
Documents when onboarded are given a short key. To allow for data to be presented in the same views, even with conflicting data names, we by convention choose the keys of an individual data item to be <document-key>_<slugified-name>, or for child objects, such as CreatureActions, <document-key>_<slugified-parent-name>_<slugified-name> which should be unique per object all cases. The only violation of this rule is on legendary actions, which are also CreatureActions, so Legendary Bite can be distinct from Bite.

**Examples:**
> srd_magic-missile - The original Magic Missile, from Wizard's of the Coast's Systems Reference Document (srd)
>
> a5e-ag_acolyte - The Acolyte Background, from Advanced 5e's Adventurer's Guide (a5e-ag).
