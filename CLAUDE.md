# CLAUDE.md

This file provides guidance to Claude Code when working with this repository. See the README for setup instructions.

## Repository Overview
* **Back-end**: Django project named `studysphere` (Django 6.0.6)
* **Front-end**: Static files in `/static` (CSS/JS/images), Media uploads in `/media`
* **Database**: SQLite (`db.sqlite3`)
* **Caching**: Redis with `redis://127.0.0.1:6379/1`

## Common Commands
**Development Server**
`python manage.py runserver`

**Database Migrations**
`python manage.py makemigrations`
`python manage.py migrate`

**Django Admin**
`python manage.py createsuperuser`

**Dependency Resolution**
`pip install -r requirements.txt`

## Code Structure
1. **Django Apps**
   - `accounts/` - User management, authentication, profiles
   - `groups/` - Group functionality, group chats
   - `messaging/` - Direct messaging system
   - `notifications/` - Notification system
   - `friends/` - Friendship/social connections
   - `studySessions/` - Study session management

2. **Project Structure**
   - `studysphere/` - Main Django project (settings, URLs, ASGI/WSGI)
   - `templates/` - Django templates for HTML rendering
   - `static/` - Static assets (CSS, JavaScript, images)
   - `media/` - User-uploaded files

3. **Real-time Features**
   - Uses Django Channels for WebSocket support
   - Redis as the channel layer backend
   - ASGI application configured in `studysphere/asgi.py`

## Development Notes
- Virtual environment located at `.venv/` - activate with `source .venv/bin/activate`
- Environment variables managed in `.env` file (contains SECRET_KEY, etc.)
- Static files collected to `staticfiles/` directory for production
- Media files stored in `media/` directory

## Next Steps
* Review individual app directories (`accounts/`, `groups/`, etc.) for specific functionality
* Check `requirements.txt` for exact dependency versions
* Examine template files for frontend structure and styling approaches