#!/bin/sh
set -eu

python <<'PY'
import os
import sys
import time

host = os.environ.get("POSTGRES_HOST")
if not host:
    sys.exit(0)

import psycopg

dsn = (
    f"host={host} "
    f"port={os.environ.get('POSTGRES_PORT', '5432')} "
    f"dbname={os.environ.get('POSTGRES_DB', 'fleet')} "
    f"user={os.environ.get('POSTGRES_USER', 'fleet')} "
    f"password={os.environ.get('POSTGRES_PASSWORD', 'fleet')}"
)

last_error = None
for _ in range(30):
    try:
        with psycopg.connect(dsn, connect_timeout=2):
            sys.exit(0)
    except psycopg.OperationalError as exc:
        last_error = exc
        time.sleep(1)

sys.stderr.write(f"Postgres did not accept connections: {last_error}\n")
sys.exit(1)
PY

python manage.py migrate --noinput
exec "$@"
