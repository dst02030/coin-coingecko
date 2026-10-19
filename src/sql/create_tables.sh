#!/bin/bash
set -euo pipefail
: "${DB_HOST:?Set DB_HOST}" "${DB_PORT:?Set DB_PORT}" "${DB_USER:?Set DB_USER}"
: "${DB_NAME:?Set DB_NAME}" "${DB_PASSWORD:?Set DB_PASSWORD}"
file_path="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/create_sql"
export PGPASSWORD="$DB_PASSWORD"
for sql in "$file_path"/schema_*.sql "$file_path"/table_*.sql; do
    psql -X --set=ON_ERROR_STOP=1 --host="$DB_HOST" --port="$DB_PORT" \
        --username="$DB_USER" --dbname="$DB_NAME" --file="$sql"
done
