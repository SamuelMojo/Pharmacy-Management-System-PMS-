# Pharmacy Management System (PMS)

Desktop application for Crossroads Community Pharmacy (CCP). It manages medicine stock, supplier orders, prescriptions, billing, complaints and reports, with role-based access and an audit log of every critical action.

Built with Python 3.13, PySide6 and PostgreSQL.

## What you need installed

| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.13 | Everyone must use 3.13 |
| Git | latest | |
| VS Code | latest | With the Microsoft Python extension. PyCharm also works |
| Docker Desktop | latest | Runs the database (needed from the database step onwards) |

Mac: `brew install python@3.13 git` and `brew install --cask docker`
Windows: `winget install Python.Python.3.13`, `winget install Git.Git` and `winget install Docker.DockerDesktop`

## Getting started

Mac:

```
git clone https://github.com/SamuelMojo/Pharmacy-Management-System-PMS-.git
cd Pharmacy-Management-System-PMS-
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```
git clone https://github.com/SamuelMojo/Pharmacy-Management-System-PMS-.git
cd Pharmacy-Management-System-PMS-
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

Activate the virtual environment in every new terminal. Your prompt should start with `(.venv)`.

## Run the app

```
python -m pms.main
```

A login window opens. Log in as `admin` (see Database above).

## Run the tests

```
docker compose up -d
pytest
```

Tests that use the database run against a separate database called `pms_test`, never your real data. If PostgreSQL is not running those tests are skipped.

How the foundation works, and how to add your own screens, tables and permissions: see `docs/foundation-guide.md`.

## Database

The database is PostgreSQL, run in Docker. Docker Desktop must be open.

```
cp .env.example .env          # Windows: copy .env.example .env
docker compose up -d
python -m pms.migrate --seed
```

`.env` is ignored by Git, so never commit it. `python -m pms.migrate` builds the tables from the numbered files in `migrations/` (safe to run again; it only applies new files). `--seed` adds one demo user per role.

Demo logins (password `Pharmacy2026` for all): `admin`, `pharmacist`, `stock`, `finance`, `counter`.

After a `git pull` that adds a new file to `migrations/`, run `python -m pms.migrate` again.

## Project structure

| Folder | Contents |
| --- | --- |
| `pms/ui` | PySide6 screens |
| `pms/service` | Business rules and role checks |
| `pms/dao` | Database access (SQL) |
| `pms/model` | Data classes (Medicine, Patient, Prescription...) |
| `pms/security` | Login, roles and audit log |
| `migrations` | Numbered SQL files that build the database tables |
| `tests` | pytest tests |
| `docs` | UML diagrams and the test plan |

## Team workflow

- Never commit directly to `main`. Work on a branch named `feature/<component>-<task>`.
- Open a pull request. Another team member must review it before it is merged.
- Run `pytest` before you push.
- To add a library: `pip install <name>`, then `pip freeze > requirements.txt`, and commit the change.
- After any pull that changes `requirements.txt`, run `pip install -r requirements.txt` again.
- Do not hard-code file paths. Use `pathlib.Path`.
- Never commit passwords or your `.env` file.

## Team

| Name | Component |
| --- | --- |
| Samuel | Accounts, security and project foundation |
| (name) | Medicine, stock and orders |
| (name) | Prescriptions, patients and requests |
| (name) | Payments, billing and complaints |
| (name) | Reports and testing |
