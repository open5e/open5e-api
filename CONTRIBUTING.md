# Contributing

This project is open to contributions from anyone. If you have a suggestion, a bug fix, a new feature, expanded content, or anything else, feel free to open an issue or a pull request. This
document will guide you through the process of contributing to the project.

## Table of Contents
- [Overall Process](#overall-process)
- [Data Contributions](#data-contributions)
- [Code Contributions](#code-contributions)

## Overall Process
To ensure that your contribution can be accepted and merged we recommend the following process. Many of these steps can
be done in parallel, and some may not be necessary depending on the size of the contribution.

### Talk to Us
The project is currently undergoing many changes, and we want to make sure that your contribution can be accepted and 
does not conflict with any ongoing work. This can be done via an 
[issue](https://github.com/open5e/open5e-api/issues/new) on this repository or by joining our 
[Discord](https://discord.gg/QXqF6gSVqB) and talking to us there. Good and clear communication throughout the process will help 
ensure that your contribution can be accepted.

It is also a good idea to check the [issues](https://github.com/open5e/open5e-api/issues) and 
[pull requests](https://github.com/open5e/open5e-api/pulls) to see if anyone else is working on something similar.

### Set Up Your Environment
In order to be able to contribute you will need to set up your local development environment. Follow the instructions in
the [README](./README.md) to get started.

### Contribute Changes
In order to make your changes follow the steps below:

1. [Fork the repository](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo)
2. Create a new branch for your changes
3. Make your changes
4. Test your changes
5. Commit your changes
6. Push your changes to your fork
7. [Open a pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request)
8. Respond to any feedback. This is crucial to ensure that your changes can be merged.
9. Wait for your changes to be merged. This may take some time, so be patient. If you have not heard back in a few days, feel free to ask for an update.
10. Celebrate!
11. Update your fork
12. Delete your branch

If you have no experience working with Git or GitHub, you can find a guide on GitHub [here](https://guides.github.com/activities/hello-world/)
and on Git [here](https://docs.github.com/en/get-started/using-git/about-git).

## Data Contributions
Data contributions are a great way to help expand the content available in the API. This can be anything from adding new
sources, fixing errors, or expanding existing content.

### Version `v1` vs `v2`
The API has two distinct versions, `v1` and `v2`. As of 2024-04-08, `v1` is the dataset exclusively used in production,
so contributing data to `v1` can get your changes live faster and for some resources is the only option at the moment. 
However, the migration to `v2` is ongoing, and for some resources `v2` is the better option. If you are unsure which
version to contribute to, feel free to ask us.

The process of editing and adding data is different for each version, so make sure to follow the correct instructions.

### Adding a new source
A new source is a new book or other publication which contains content published with an Open License. Adding new sources
have to be registered first in the data set and then the content can be added. Furthermore, it is important to link
the source to the license it was published under where possible. Otherwise, link to a page that shows the license.
#### Version `v1`
To add a new source, create a new directory inside `data/v1` and a `Document.json` file that credits the source and
links to the license it was published under. An example of this can be found [here](./data/v1/wotc-srd/Document.json).
Make sure that the folder name matches up with the value of the `slug` field in the `Document.json` file. The 
slug needs to be unique across all source. Best to ask us before setting this.

#### Version `v2`
In `v2` a new source can be added via the [admin interface](./docs/v2/admin_interface.md). Create a new document
and fill out all the fields with the appropriate information. Once the document is created, you can associate
it with the content you add.

- `Name`: The name of the source. Use the full name of the published document.
- `Desc`: A description of the source. Use the blurb on the sources website or give a brief overview of what it is.
- `Key`: A unique key for the source. Make sure to talk to us before setting this. It should be a short, unique identifier.
- `License`: The license the source was published under. Select one of the available licenses. If the license is not available, 
  create a new one.
- `Publisher`: The publisher of the source. Select one of the available publishers. If the publisher is not available, 
  create a new one.
- `Ruleset`: The ruleset the source is associated with. Select one of the available rulesets. If the ruleset is not available, 
  create a new one.
- `Author`: The author of the source. This can be a single author or a list of authors. List them in the format `Author 1, Author 2, Author 3`.
- `Published at`: The Date and Time the source was published. Select the date it was published on. The time can be set to 00:00:00.
- `Permalink`: A link to the source. This can be a link to the publishers website, a page on the publishers website, or a page that 
  contains the license information. Make sure to choose a link that is unlikely to change.

Once you've created the document (and publisher if it did not exist yet), export the data. This will create a new directory
in the `data/v2` folder with the source information. You can then add the content to the source.


### Adding / Editing Content
Adding or editing content is the process of adding or changing the actual game content.

We recommend using an editor like [VS Code](https://code.visualstudio.com/) to make changes to the files. 
This will help you catch any syntax errors and make it easier to navigate the data.

Additionally, make sure to check your data by running the API locally and see if there are any issues with the display.

And finally, make sure to commit your changes in small, logical steps. 
This will make it easier for us to review your changes.

#### Version `v1`
In `v1` all changes are made directly in the JSON files. Each resource type has its own file in the 
`data/v1/{document-slug}` directory.

When editing content, make sure to follow the structure of the existing content. This includes the fields that are
available and the format of the data. If you are adding new content, make sure to add it to the correct file and
follow the structure of the existing content.

The following resource types are available in `v1`:

- `Archetype`
- `Armor`
- `Background`
- `CharClass`
- `Condition`
- `Feat`
- `MagicItem`
- `Monster`
- `MonsterSpell`
- `Race`
- `Section`
- `Spell`
- `SpellList`
- `Subrace`
- `Weapon`

If you are unsure where to add your content or how to structure it, feel free to ask us.

#### Version `v2`
In `v2` changes can also be made via the [admin interface](./docs/v2/admin_interface.md) or by editing the exported 
JSON files. In the admin interface just navigate to the resource you want to edit and make your changes or add a new
resource of a specific type.

Currently, the following resources are available via the admin interface:

- `Alignment`
- `Armor`
- `Background`
- `Character class`
- `Condition`
- `Creature set`
- `Creature type`
- `Creature`
- `Damage type`
- `Feat`
- `Feature item`
- `Feature`
- `Item category`
- `Item rarity`
- `Item set`
- `Item`
- `Language`
- `Race`
- `Size`
- `Spell school`
- `Weapon`

If you are unsure where to add your content or how to structure it, feel free to ask us. Other resources cannot 
currently be added to the API in `v2`. This list will be expanded as the migration progresses.

## Code Contributions
Code contributions are welcome, but a bit more complex. The project is built using Django and Django Rest Framework, so you will need to have some experience with these technologies. 
If you are new to Django, you can find a tutorial [here](https://docs.djangoproject.com/en/5.0/).

With code changes it is very important to talk to us first. We want to make sure that your changes are in line with the 
project goals and that they do not conflict with any ongoing work.

### Changing Models
Models such as Monsters and Classes are stored in the [api/models](/api/models) directory. 
These define fields (hp, str, speed) and how they are output. The import of Game Content from `data` 
is handled by django's built-in [loaddata](https://docs.djangoproject.com/en/4.2/ref/django-admin/#django-admin-loaddata).