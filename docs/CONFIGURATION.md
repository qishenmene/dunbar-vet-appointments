# Configuration management

## Principles

1. **No secrets in version control.** The `.env` file is git-ignored; only
   `.env.example` with illustrative values is committed.
2. **Same artefact, environment-specific settings.** `config.py` selects a
   configuration class from the `APP_ENV` environment variable
   (`development`, `testing`, `production`).
3. **Reproducible dependencies.** `requirements.txt` pins exact versions.
4. **Local-first operation.** The app uses SQLite and listens on localhost by
   default, so the appointment book keeps working when the clinic's internet
   is down.
5. **Every change reviewed.** Code and configuration changes move through
   pull requests, CI and the changelog.

## Configuration items

| Variable | Default (dev) | Purpose |
| -------- | ------------- | ------- |
| `APP_ENV` | `development` | Selects config class: development / testing / production |
| `SECRET_KEY` | dev placeholder | Flask session signing; **must** be set to a random value in production |
| `DATABASE_PATH` | `dunbar_vet.sqlite3` | SQLite file (inside the git-ignored `instance/` folder unless absolute) |
| `HOST` | `127.0.0.1` | Bind address; localhost only by default |
| `PORT` | `5000` | Dev server port; production waitress uses `8000` in the scripts |

## Configuration items in version control

- Application settings: `config.py`
- Sample environment file: `.env.example`
- Dependencies (software bill of materials): `requirements.txt`
- CI pipeline: `.github/workflows/ci.yml`
- Deployment scripts: `scripts/*.bat`, `scripts/*.sh`
- Line-ending/attributes policy: `.gitattributes`
- Ignored artefacts policy: `.gitignore`

## Local setup

Copy `.env.example` to `.env` (done automatically by `scripts/setup.*`) and
change `SECRET_KEY` for any non-development use. Initialise the database with:

```bash
flask --app run.py init-db
```

## Versioning and change records

- Code versions: Git tags, semantic versioning
- Change history: `CHANGELOG.md` (Keep a Changelog format)
- Change process: branch per story → pull request → review → CI → merge
- Release records: GitHub Releases per tag

## Backup / recovery (operational note)

The only stateful artefact is the SQLite file. Back it up by copying the file;
the application can be rebuilt from any clean checkout plus a restored database
file. No external services are part of the runtime.
