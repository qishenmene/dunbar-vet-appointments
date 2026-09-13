# Branching strategy and contribution workflow

This document defines the version control rules for the team and is evidence
for the Assessment 2 configuration management report.

## Branch model

A simplified **Git Flow / trunk-based hybrid** is used:

| Branch | Purpose | Who can commit |
| ------ | ------- | -------------- |
| `main` | Release-ready code. Every merge is tagged (e.g. `v0.1.0`). | No direct commits — pull request only |
| `develop` | Integration branch for the current sprint | Pull request only |
| `feature/<story-id>-<short-desc>` | One user story's work (e.g. `feature/DV-12-add-client-records`) | Story owner |
| `bugfix/<story-id>-<short-desc>` | Non-urgent defects found before release | Bug owner |
| `hotfix/<short-desc>` | Emergency fixes to `main`, merged back to both `main` and `develop` | Bug owner |
| `release/x.y.z` | Release preparation (changelog, version bumps) | Release manager |

### Rules

1. Create every feature branch from the latest `develop`.
2. A branch maps to **one user story** (its Jira id is in the branch name),
   matching the project Definition of Done.
3. Keep branches short-lived; rebase or merge `develop` in regularly.
4. Merge with a **pull request** that references the story id (`Closes DV-12`).
5. A pull request requires:
   - at least **one approving review** from another team member;
   - all review comments addressed;
   - green CI (tests pass);
   - the Definition of Done checklist in the PR template completed.
6. `main` and `develop` are protected branches (no force pushes, no deletion,
   PR + review required).
7. Releases on `main` are tagged with semantic version numbers and recorded in
   `CHANGELOG.md`.

## Commit message convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <short imperative summary>

<optional body explaining what and why>

Refs: DV-12
```

Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`, `ci`, `perf`.

Examples:

```
feat(clients): add create and search for client records
test(appointments): cover 15-minute slot validation for consultations
docs(cm): document environment configuration
chore: pin dependency versions in requirements.txt
```

- Small, focused commits; never commit secrets or `.env`.
- Reference the story id so history is traceable to the backlog.
- User-visible changes get an entry in `CHANGELOG.md`.

## Standard workflow

```bash
git switch develop
git pull
git switch -c feature/DV-12-add-client-records
# ...work...
git add <files>
git commit -m "feat(clients): add client record creation"
git push -u origin feature/DV-12-add-client-records
# Open a pull request into develop on GitHub, request a teammate's review
```

After approval and CI: **Squash and merge** into `develop` (the squash commit
keeps history readable); release merges to `main` use a merge commit.

## Tags / releases

`vMAJOR.MINOR.PATCH` (semantic versioning):

- `v0.x.y` during development; `v1.0.0` at first handover.
- Each tag gets a GitHub Release with notes copied from the changelog.
