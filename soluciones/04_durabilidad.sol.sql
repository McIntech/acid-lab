-- =====================================================================
-- SOLUCIÓN 04 — DURABILIDAD
-- =====================================================================
-- Este .sql cubre el PASO 1 (emitir + COMMIT) y el PASO 3 (comprobar).
-- El PASO 2 (reiniciar el servidor) es un comando de shell, no SQL.
--
-- Secuencia completa (cópiala en tu terminal):
--
--   PSQL="/opt/homebrew/opt/postgresql@17/bin/psql"
--   DSN="dbname=postgres user=postgres host=localhost"
--   ./reset.sh
--   $PSQL "$DSN" -f soluciones/04_durabilidad.sol.sql   # paso 1 (commit)
--   brew services restart postgresql@17                  # paso 2 (reinicio)
--   sleep 2
--   $PSQL "$DSN" -c "SELECT count(*) FROM facturas;"      # paso 3 => 1
--
-- Por qué sobrevive: en el COMMIT, el registro va al WAL y se hace fsync
-- a disco (synchronous_commit=on). Aunque el proceso muera justo después,
-- al arrancar Postgres REPRODUCE el WAL (crash recovery) y la factura
-- reaparece. El WAL es el contrato de durabilidad.
-- =====================================================================

-- PASO 1: emitir y CONFIRMAR la factura.
BEGIN;
INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid());
COMMIT;

-- PASO 3 (también corre aquí, antes del reinicio, para ver el estado):
SELECT count(*) AS facturas_confirmadas FROM facturas;  -- => 1
-- ...reinicia el servidor (paso 2) y vuelve a correr este SELECT: sigue 1.
