# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview
StudySphere is a Django + Django Channels social study platform: user profiles, friends, direct messaging, study groups (with real-time chat and voice), study sessions, and flashcards.

* **Django 4.2** (`requirements.txt` pins `Django~=4.2`; the "6.0.6" in generated docstrings is boilerplate — ignore it).
* **Python 3.13** (`mise.toml`, `render.yaml`).
* **Real-time**: Django Channels 4 over ASGI, served by Daphne/Uvicorn.
* **Database**: resolved via `dj_database_url` — SQLite (`db.sqlite3`) locally, Postgres in production through `DATABASE_URL`.
* **Redis is optional**: channel layer and cache are only wired up when `REDIS_URL` is set (see `settings.py`). Without it, Channels falls back to the in-memory layer — fine for single-process dev, but group/voice fan-out won't work across processes.

## Common Commands
```bash
source .venv/bin/activate           # virtualenv lives at .venv/
python manage.py runserver          # dev server
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --no-input
pip install -r requirements.txt
```

There is **no test suite** in this repo and no lint config — do not assume `manage.py test` covers anything.

`build.sh` (used by Render) runs collectstatic, then `makemigrations --check --dry-run` (build fails if models changed without a committed migration), then `migrate`. Run `makemigrations --check --dry-run` locally before committing model changes to avoid breaking the build.

## Architecture Notes (non-obvious)

**App layout.** Apps: `accounts`, `friends`, `messaging`, `groups`, `studySessions`, `flashcards`, `notifications`.
* The `notifications/` app is **vestigial** — it has no `models.py`. The actual `Notification` model (plus `Profile` and `FriendRequest`) lives in **`accounts/models.py`**. Look there, not in `notifications/`.
* Several apps contain a nested duplicate project package (e.g. `accounts/accounts/`, `groups/groups/`, `messaging/messaging/` with their own `settings.py`/`asgi.py`/`manage.py`). These are leftover `startproject`/`startapp` artifacts and are **not used** — the only live project package is the top-level `studysphere/`. Ignore them.

**WebSockets.** `studysphere/asgi.py` composes `websocket_urlpatterns` from `groups`, `messaging`, and `studySessions` routing modules under `AuthMiddlewareStack`. Consumers:
* `groups/consumers.py` — `GroupChatConsumer` (`ws/group/<uuid>/`) and `VoiceConsumer` (`ws/voice/<uuid>/`).
* `messaging/consumers.py`, `studySessions/consumers.py`.
Any new real-time feature needs a `consumers.py` + `routing.py` and its patterns added to the `URLRouter` in `asgi.py`.

**URLs & namespaces.** Root URLs in `studysphere/urls.py` mount each app under a namespace (`accounts`, `messaging`, `groups`, `friends`, `flashcards`, `study_sessions`). Use `{% url 'namespace:name' %}` / `reverse('namespace:name')`. Media is served via a `re_path` to `django.views.static.serve` **in all environments** (not just DEBUG).

**Custom error handlers**: `handler400/403/404/500` → `studysphere/views.custom_*` (templates under `templates/errors/`).

**Maintenance mode**: `MaintenanceModeMiddleware` (`studysphere/middleware.py`) returns `errors/503.html` for all non-`/admin/` requests when `MAINTENANCE_MODE=True`.

**Profiles auto-create**: a `post_save` signal on `User` in `accounts/signals.py` creates/ensures a `Profile`. Registered via `AccountsConfig`.

**Notification badge**: `accounts/context_processors.notifications_context` injects `unread_notif_count` into every template; it's registered in `TEMPLATES` context processors.

**Templates**: primary backend is Django templates (`APP_DIRS=True` + top-level `templates/`). A Jinja2 environment (`studysphere/jinja2.py`) exists but is not wired into `TEMPLATES` — Django templating is what's active.

**Storage**: `django-storages`/`boto3` are installed and `storages` is in `INSTALLED_APPS`, but S3 is **not configured** — the project uses local `MEDIA_ROOT` (it was migrated off AWS). WhiteNoise (`CompressedManifestStaticFilesStorage`) serves static files.

## Configuration
Environment variables (via `.env` locally, Render env in prod): `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` (space-separated), `DATABASE_URL`, `REDIS_URL`, `MAINTENANCE_MODE`. `.env`, `db.sqlite3`, `BACKUP.db.sqlite3`, `/staticfiles/`, and `/media/*` (except the default avatar) are gitignored.

## Deployment
`render.yaml` defines a web service (`gunicorn studysphere.asgi:application -k uvicorn.workers.UvicornWorker`), a Redis instance, and a Postgres database. `DEBUG=False` and `ALLOWED_HOSTS=.onrender.com` in production.
