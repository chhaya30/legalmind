#!/usr/bin/env sh
set -eu
mkdir -p /backups
export PGPASSWORD="${POSTGRES_PASSWORD:-legalmind}"
pg_dump -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER:-legalmind}" -d "${POSTGRES_DB:-legalmind}" > "/backups/legalmind_$(date +%Y%m%d_%H%M%S).sql"
