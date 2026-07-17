#!/usr/bin/env bash
# exit on error
set -o errexit

pip install "uvicorn[standard]==0.34.0"
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate