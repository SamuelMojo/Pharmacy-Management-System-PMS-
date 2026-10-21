# Pharmacy Management System (PMS)

Desktop application for Crossroads Community Pharmacy (CCP). It manages medicine stock, supplier orders, prescriptions, billing, complaints and reports, with role-based access and an audit log of every critical action. There is no real payment processing: receipts only.

Built with Python 3.13, PySide6 and PostgreSQL (in Docker).

## Contents

1. [What you need installed](#what-you-need-installed)
2. [First-time setup](#first-time-setup)
3. [Run the app](#run-the-app)
4. [Run the tests](#run-the-tests)
5. [Database](#database)
6. [Project structure](#project-structure)
7. [Who can do what](#who-can-do-what)
8. [Adding your own work](#adding-your-own-work)
9. [Git workflow](#git-workflow)
10. [Rules](#rules)
11. [Troubleshooting](#troubleshooting)
12. [Team](#team)

## What you need installed

| Tool | Version | Notes |
| --- | --- | --- |
| Python | 3.13 | Everyone must use 3.13 |
| Git | latest | |
| VS Code | latest | With the Microsoft Python extension |
| Docker Desktop | latest | Runs the database. Open it and wait until it says it is running |

Mac: `brew install python@3.13 git` and `brew install --cask docker`

Windows: `winget install Python.Python.3.13`, `winget install Git.Git` and `winget install Docker.DockerDesktop`

## First-time setup

Mac:

```
git clone https://github.com/SamuelMojo/Pharmacy-Management-System-PMS-.git
cd Pharmacy-Management-System-PMS-
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d
python -m pms.migrate --seed
```

Windows (PowerShell):

```
git clone https://github.com/SamuelMojo/Pharmacy-Management-System-PMS-.git
cd Pharmacy-Management-System-PMS-
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
docker compose up -d
python -m pms.migrate --seed
```

If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

Activate the virtual environment in every new terminal (`source .venv/bin/activate` on Mac). Your prompt should start with `(.venv)`.

## Run the app

```
python -m pms.main
```

A login window opens. Log in with one of the demo accounts below.

| Username | Role |
| --- | --- |
| `admin` | System manager |
| `pharmacist` | Lead pharmacist |
| `stock` | Stock manager |
| `finance` | Finance manager |
| `counter` | Medicine counter assistant |

The password for all of them is `Pharmacy2026`. They are for development and the demo only.

## Run the tests

```
docker compose up -d
pytest
```

Tests that use the database run against a separate database called `pms_test`, never your real data. It is created automatically. If PostgreSQL is not running, those tests are skipped with a message.

## Database

PostgreSQL runs in Docker. Settings are in `.env` (copied from `.env.example`). `.env` is ignored by Git, so never commit it.

| Command | What it does |
| --- | --- |
| `docker compose up -d` | Start the database |
| `docker compose down` | Stop it (your data is kept) |
| `docker ps` | List running containers; you should see `pms-db` |
| `python -m pms.migrate` | Build or update the tables from the files in `migrations/` |
| `python -m pms.migrate --seed` | Same, and also create the demo users |

Tables are built by numbered SQL files in `migrations/`. After a `git pull` that adds a new file there, run `python -m pms.migrate` again. It is safe to run repeatedly: it only applies files that have not run yet.

To add your own tables, create `migrations/00N_yourthing.sql` (agree the number in the group chat; duplicate numbers are refused). Never edit a migration after it has been committed. Add a new numbered file instead.

## Project structure

Code flows one way: **ui → service → dao → database**. Never skip a layer.

| Folder | Contents |
| --- | --- |
| `pms/ui/<yourfolder>` | PySide6 screens only. No SQL, no business rules |
| `pms/service/<yourfolder>` | Business rules, permission checks, audit logging |
| `pms/dao/<yourfolder>` | SQL only, one function per query |
| `pms/model/<yourfolder>` | Data classes (Medicine, Patient, Prescription...) |
| `pms/security` | Passwords, permissions, audit log, notifications, session |
| `migrations` | Numbered SQL files that build the database tables |
| `tests` | pytest tests |
| `docs` | UML diagrams, test plan, and `foundation-guide.md` |

Each developer works in their own sub-folders (for example `ui/stock/`, `service/stock/`, `dao/stock/`) so merge conflicts stay rare.

## Who can do what

Defined in `pms/security/permissions.py`. The system manager can do everything.

| Action | Counter | Stock | Finance | Pharmacist |
| --- | --- | --- | --- | --- |
| View stock | Yes | Yes | Yes | Yes |
| Manage stock, place supplier orders | No | Yes | No | No |
| Process a sale | Yes | No | No | No |
| Refund, pay suppliers, view payments | No | No | Yes | No |
| Log a patient, verify a prescription | Yes | No | No | Yes |
| Sign off restricted medicines, manage complaints | No | No | No | Yes |
| Log a complaint | Yes | No | No | Yes |
| View reports | No | Yes | Yes | Yes |
| Manage users, view audit log | No | No | No | No |

## Adding your own work

Full guide with code examples: [`docs/foundation-guide.md`](docs/foundation-guide.md). In short:

1. **Table:** add `migrations/00N_name.sql`, then run `python -m pms.migrate`.
2. **DAO:** SQL functions that take a `conn`. Use `%s` placeholders, never f-strings with user input.
3. **Service:** start with `require(actor, Action.X)`, do the work inside `with database.transaction() as conn:`, and call `audit.log_action(..., conn=conn)` for every critical action.
4. **Notification:** `notifications.notify(title, message, role=Role.X, conn=conn)`.
5. **Screen:** write a `QWidget`, then list it in `pms/ui/<yourfolder>/screens.py` with the permission it needs. The sidebar picks it up automatically. If it has a `refresh()` method, it is called each time the screen opens.
6. **Tests:** put them in `tests/`. Use the `db`, `make_user` and `admin` fixtures from `tests/conftest.py`, and `qtbot` for screens.

## Git workflow

Never commit directly to `main`. Every piece of work goes on a branch and through a pull request.

**Start each work session**

```
git checkout main
git pull
pip install -r requirements.txt
python -m pms.migrate
```

**Start a new piece of work**

```
git checkout -b feature/<area>-<task>
```

Example: `git checkout -b feature/stock-medicine-catalogue`

**Save your work**

```
git status
git add .
git commit -m "Short description of what you did"
```

Check `git status` before committing. `.env`, `.venv` and `.idea` must not appear.

**Share it**

```
pytest
git push -u origin feature/<area>-<task>
```

Then on GitHub: click **Compare & pull request**, describe the change, ask a teammate to review, and click **Merge pull request** once they approve.

**Keep your branch up to date with main**

```
git checkout main
git pull
git checkout feature/<area>-<task>
git merge main
```

If Git reports a conflict, open the marked files, keep the right lines, remove the `<<<<<<<`, `=======` and `>>>>>>>` markers, then:

```
git add .
git commit
```

**Useful extras**

| Command | What it does |
| --- | --- |
| `git status` | What has changed |
| `git branch` | Which branch you are on (marked with `*`) |
| `git log --oneline -5` | Last five commits |
| `git diff` | Exactly what you changed |
| `git restore <file>` | Throw away your uncommitted changes to a file |
| `git stash` / `git stash pop` | Put changes aside, then bring them back |

## Rules

- Never commit directly to `main`. Branch names are `feature/<area>-<task>`.
- Another team member must review every pull request before it is merged.
- Run `pytest` before you push. Do not merge a failing build.
- Never commit `.env`, `.venv` or passwords.
- Keep to the layers. No SQL in screens, no business rules in DAOs.
- Start every service function with `require(actor, Action.X)`.
- Audit log every critical action, in the same transaction as the change.
- Never edit a migration after it has been committed. Add a new numbered file.
- Use `pathlib.Path` for file paths. Do not hard-code them.
- To add a library: `pip install <name>`, then `pip freeze > requirements.txt`, commit it, and tell the group. Everyone then runs `pip install -r requirements.txt`.
- Ask Samuel before changing `pms/security/`, `pms/dao/database.py` or `pms/ui/main_window.py`.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `Cannot connect to the Docker daemon` | Docker Desktop is not open. Open it and wait until it says it is running |
| `docker: unknown command: docker compose` | The Compose plugin is missing. Install Docker Desktop, or on Mac run `brew install docker-compose`, then `mkdir -p ~/.docker/cli-plugins` and `ln -sfn "$(brew --prefix)/opt/docker-compose/bin/docker-compose" ~/.docker/cli-plugins/docker-compose` |
| `Cannot reach the database` when starting the app | Run `docker compose up -d`, wait about 10 seconds, try again |
| Database tests are skipped | Docker is not running, so `pms_test` cannot be reached |
| `ModuleNotFoundError` | The venv is not active, or run `pip install -r requirements.txt` again |
| Table or column missing after a pull | Someone added a migration. Run `python -m pms.migrate` |
| `role "pms" does not exist` | Check `DB_USER` in your `.env` matches `.env.example` |
| Account locked | Five wrong passwords lock it for 15 minutes. `admin` can reset it under User accounts |
| PowerShell blocks `Activate.ps1` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then try again |

## Team

| Name | Component |
| --- | --- |
| Samuel | Accounts, security and project foundation |
| (name) | Medicine, stock and orders |
| (name) | Prescriptions, patients and requests |
| (name) | Payments, billing and complaints |
| (name) | Reports and testing |
