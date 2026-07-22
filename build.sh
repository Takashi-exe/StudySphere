#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py check_redis
python manage.py cleanup_missing_avatars

python manage.py collectstatic --no-input

# Fail the build if model changes exist without a committed migration
python manage.py makemigrations --check --dry-run

python manage.py migrate