#!/bin/bash

# Apply database migrations
python manage.py makemigrations api
python manage.py migrate --noinput

# Run Django tests
python manage.py test

# Start the Gunicorn server
exec gunicorn --bind 0.0.0.0:5000 alarm.wsgi:application &

# Start MkDocs server
cd alarm-docs
exec mkdocs serve --dev-addr 0.0.0.0:8000 &

# Start Locust load testing
cd ..
exec locust -f locusttest.py --host=https://alarm.sgt.me.uk