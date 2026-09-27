# Github Releases
We use github releases for stable packages of this software. Instructions on creating a new github release.

### Confirm Stability
First, confirm the staging branch is stable.

```
git fetch origin
git checkout staging
git pull origin staging
rm ./db.sqlite3
uv run python manage.py quicksetup
uv run python manage.py runserver
```

Then in a new window terminal run tests.
```
uv run pytest
```
If the results are successful, then you are stable and ready to mint a release.

### Keep staging and main histories aligned

`staging` is the integration branch. `main` is the production deploy pointer. CI/CD deploys on push to either branch.

- Feature PRs into `staging` may use squash merge. That keeps staging linear.
- Promoting `staging` to `main` must **never squash** and must **never rebase-merge**. Use **Create a merge commit** on the GitHub PR (or a local merge / fast-forward). Squash-merge creates new SHAs on `main` that staging does not share, so the next release PR looks huge and conflicts on already-shipped files.
- After `main` is updated, merge `main` back into `staging` so staging contains the merge commit. The two branches then share history again.

Hotfixes should land on `staging` first when possible. If a change must go to `main` directly, merge `main` back into `staging` immediately. Do not leave unique commits on `main`.

Optional GitHub setting: on the `main` branch protection/ruleset, allow merge commits only (disable squash and rebase for PRs targeting `main`). Leave squash enabled for PRs into `staging`.

### Merging staging into main

All version bumps and release-doc updates happen on `staging`. Production changes only when `staging` is merged into `main`.

First, merge main into staging to resolve any conflicts there.
```
git fetch origin
git checkout staging
git pull origin staging
git merge origin/main
(If 'already up to date', proceed, else resolve conflicts)
```

Bump the version in `pyproject.toml` (major.minor.patch) on staging. Increment the minor version if ANY feature changes were added, rather than just bugfixes.

Push staging, then open a PR from `staging` into `main`. Merge it with **Create a merge commit** — do not squash. Do not use a separate release branch.

Pushing to `main` kicks off production build and deploy. Wait for those to finish before tagging.

Then merge `main` back into `staging`:
```
git checkout staging
git pull origin staging
git merge origin/main
git push origin staging
```

### Creating the release
1. Go to [the github releases page](https://github.com/open5e/open5e-api/releases) for the repo.
1. Click Draft a New Release
1. Pick target: main. Pick Create a new tag.
1. Name the new release tag `vMAJOR.MINOR.PATCH` (same as `pyproject.toml`, with a `v` prefix).
1. Name the Release itself the same as the tag.
1. Generate the release notes.
1. Set as latest release
1. Click Publish release

Do not rely on `.github/workflows/release.yml` for this. It is stale (expects a missing `dist/` zip and `CHANGELOG.md`, and opens a draft). The real release is the GitHub Release above; production deploy is the push to `main`.
