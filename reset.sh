#!/usr/bin/env bash
# =====================================================================
# reset.sh — deja el lab en CERO: recrea tablas + seed desde schema.sql.
# Idempotente: córrelo cuantas veces quieras.
# =====================================================================
set -euo pipefail

PSQL="${PSQL:-/opt/homebrew/opt/postgresql@17/bin/psql}"
DSN="${DSN:-dbname=postgres user=postgres host=localhost}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$PSQL" ]]; then
  PSQL="$(command -v psql)"   # fallback si psql@17 ya está en PATH
fi

"$PSQL" "$DSN" -v ON_ERROR_STOP=1 -q -f "$DIR/schema.sql"
echo "✓ Lab reseteado (saldo=1, version=0, 0 facturas)."
