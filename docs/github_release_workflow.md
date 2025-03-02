# Github Releases
We use github releases for stable packages of this software. Instructions on creating a new github release.

### Confirm Stability
First, confirm the staging branch is stable.

```
git fetch origin
git checkout staging
rm ./db.sqlite3
pipenv run python manage.py quicksetup
pipenv run python manage.py runserver
```

Then in a new window terminal run tests.
```
pipenv run pytest
```
If the results are successful, then you are stable and ready to mint a release.

### Merging staging into main

First, merge main into staging to resolve any conflicts there.
```
(on branch staging)
git merge main
(If 'already up to date', proceed, else resolve conflicts)
git checkout main
git merge staging
```

At this point, locally, you'll have commits to push to origin. Doing so will kick off all build steps and deploy steps to production. It's a good idea to wait for those to finish before doing the next step.

### Creating the release
1. Go to [the github releases page](https://github.com/open5e/open5e-api/releases) for the repo.
1. Click Draft a New Release
1. Pick target: main. pick Create a new tag.
1. Name the new release tag v.major.minor.patch. Increment the minor version if ANY feature changes were added, rather than just bugfixes.
1. Name the Release itself the same as the tag.
1. Generate the release notes.
1. Set as latest release
1. Click Publish release