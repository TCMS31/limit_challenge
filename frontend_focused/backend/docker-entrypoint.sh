#!/bin/sh
set -eu

echo "Waiting for the database..."
python <<'PY'
import os
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import django
from django.db import connection
from django.db.utils import OperationalError

django.setup()

for _ in range(30):
    try:
        connection.ensure_connection()
        break
    except OperationalError:
        time.sleep(1)
else:
    raise SystemExit("Database did not become ready in time.")
PY

python manage.py migrate --noinput
python manage.py seed_submissions
exec "$@"
