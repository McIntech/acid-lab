#!/usr/bin/env bash
# =====================================================================
# verificar.sh — corre las SOLUCIONES de referencia (carpeta soluciones/)
# y reporta PASS/FAIL por reto contra el criterio de éxito de cada uno.
#
# Sirve para: (1) confirmar que el lab está sano, y (2) mostrarte cómo se
# ve un PASS. Para checar TU versión, edita el reto y corre su comando
# "CÓMO CORRER", o copia tu solución sobre la de soluciones/ y vuelve a
# correr este script.
#
# OJO: el reto 04 (durabilidad) REINICIA el servidor Postgres.
# =====================================================================
set -uo pipefail

PSQL="${PSQL:-/opt/homebrew/opt/postgresql@17/bin/psql}"
PY="${PY:-$HOME/.venvs/cli-tools/bin/python}"
DSN="${DSN:-dbname=postgres user=postgres host=localhost}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PGISREADY="/opt/homebrew/opt/postgresql@17/bin/pg_isready"
[[ -x "$PSQL" ]] || PSQL="$(command -v psql)"
[[ -x "$PGISREADY" ]] || PGISREADY="$(command -v pg_isready)"

fallos=0

scalar() { "$PSQL" "$DSN" -tAqc "$1" 2>/dev/null | tr -d '[:space:]'; }
reset()  { "$PSQL" "$DSN" -q -v ON_ERROR_STOP=1 -f "$DIR/schema.sql" >/dev/null; }

report() { # report <reto> <ok?> <detalle>
  if [[ "$2" == "1" ]]; then
    printf "  \033[32mPASS\033[0m  %-22s %s\n" "$1" "$3"
  else
    printf "  \033[31mFAIL\033[0m  %-22s %s\n" "$1" "$3"
    fallos=$((fallos + 1))
  fi
}

echo "==================== VERIFICACIÓN acid-lab ===================="

# --- 01 ATOMICIDAD: tras el fallo simulado, rollback completo ---------
reset
"$PSQL" "$DSN" -q -f "$DIR/soluciones/01_atomicidad.sol.sql" >/dev/null 2>&1
f=$(scalar "SELECT count(*) FROM facturas"); s=$(scalar "SELECT saldo FROM clientes WHERE id=1")
[[ "$f" == "0" && "$s" == "1" ]] && ok=1 || ok=0
report "01 atomicidad" "$ok" "facturas=$f saldo=$s (esperado 0/1)"

# --- 02 CONSISTENCIA: constraints activas + insert legal entra --------
reset
"$PSQL" "$DSN" -q -f "$DIR/soluciones/02_consistencia.sol.sql" >/dev/null 2>&1
chk=$(scalar "SELECT count(*) FROM pg_constraint WHERE conrelid='clientes'::regclass AND contype='c'")
uni=$(scalar "SELECT count(*) FROM pg_constraint WHERE conrelid='clientes'::regclass AND contype='u'")
fk=$(scalar  "SELECT count(*) FROM pg_constraint WHERE conrelid='facturas'::regclass AND contype='f'")
nn=$(scalar  "SELECT count(*) FROM information_schema.columns WHERE table_name='clientes' AND column_name IN ('nombre','saldo') AND is_nullable='NO'")
legal=$(scalar "SELECT count(*) FROM clientes WHERE rfc='LEGA010101AAA'")
[[ "$chk" -ge 1 && "$uni" -ge 1 && "$fk" -ge 1 && "$nn" == "2" && "$legal" == "1" ]] && ok=1 || ok=0
report "02 consistencia" "$ok" "check=$chk unique=$uni fk=$fk notnull=$nn legal=$legal"

# --- 03 AISLAMIENTO: SERIALIZABLE -> 1 factura, saldo 0 ---------------
reset
"$PY" "$DIR/soluciones/03_aislamiento.sol.py" >/dev/null 2>&1
f=$(scalar "SELECT count(*) FROM facturas"); s=$(scalar "SELECT saldo FROM clientes WHERE id=1")
[[ "$f" == "1" && "$s" == "0" ]] && ok=1 || ok=0
report "03 aislamiento" "$ok" "facturas=$f saldo=$s (esperado 1/0)"

# --- 04 DURABILIDAD: factura commiteada sobrevive al reinicio ---------
reset
"$PSQL" "$DSN" -q -f "$DIR/soluciones/04_durabilidad.sol.sql" >/dev/null 2>&1
echo "  ...reiniciando postgresql@17 para probar durabilidad..."
brew services restart postgresql@17 >/dev/null 2>&1
for _ in $(seq 1 30); do "$PGISREADY" -h localhost -q && break; sleep 0.5; done
f=$(scalar "SELECT count(*) FROM facturas")
[[ "$f" == "1" ]] && ok=1 || ok=0
report "04 durabilidad" "$ok" "facturas tras reinicio=$f (esperado 1)"

# --- 05 PESIMISTA: FOR UPDATE -> 1 factura, saldo 0 ------------------
reset
"$PY" "$DIR/soluciones/05_pesimista.sol.py" >/dev/null 2>&1
f=$(scalar "SELECT count(*) FROM facturas"); s=$(scalar "SELECT saldo FROM clientes WHERE id=1")
[[ "$f" == "1" && "$s" == "0" ]] && ok=1 || ok=0
report "05 pesimista" "$ok" "facturas=$f saldo=$s (esperado 1/0)"

# --- 06 OPTIMISTA: version-check -> 1 factura, saldo 0, version 1 -----
reset
"$PY" "$DIR/soluciones/06_optimista.sol.py" >/dev/null 2>&1
f=$(scalar "SELECT count(*) FROM facturas"); s=$(scalar "SELECT saldo FROM clientes WHERE id=1"); v=$(scalar "SELECT version FROM clientes WHERE id=1")
[[ "$f" == "1" && "$s" == "0" && "$v" == "1" ]] && ok=1 || ok=0
report "06 optimista" "$ok" "facturas=$f saldo=$s version=$v (esperado 1/0/1)"

echo "=============================================================="
if [[ "$fallos" == "0" ]]; then
  echo "TODO PASA ✓  (6/6 retos)"
else
  echo "$fallos reto(s) en FAIL ✗"
fi
reset >/dev/null
exit "$fallos"
