-- =====================================================================
-- 01 — ATOMICIDAD  (la "A" de ACID)
-- =====================================================================
--
-- 1) CONTEXTO
--    Emitir una factura son DOS pasos: (a) INSERT en facturas y
--    (b) UPDATE clientes SET saldo = saldo - 1. Si el segundo paso falla
--    a mitad, la factura ya quedó pero el timbre NO se descontó: el
--    Contador Pérez facturó GRATIS. Caja descuadrada.
--
-- 2) CONCEPTO
--    Atomicidad = "todo o nada": los dos pasos se aplican juntos o no se
--    aplica ninguno. No existen estados intermedios visibles.
--
-- ---------------------------------------------------------------------
-- 3) EL FALLO  (corre el archivo TAL CUAL y verás el bug)
-- ---------------------------------------------------------------------
-- En psql el autocommit está ENCENDIDO: cada statement se confirma solo.
-- El INSERT se confirma; el UPDATE revienta (división por cero que
-- simula un fallo a mitad) y NO hay quien revierta el INSERT.
--
--    ▼▼▼ EL FALLO — comenta este bloque cuando vayas a resolver ▼▼▼
INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid());
UPDATE clientes SET saldo = saldo - (1 / 0) WHERE id = 1;  -- 💥 falla aquí
--    ▲▲▲ FIN EL FALLO ▲▲▲
--
-- Ahora inspecciona el desastre:
SELECT count(*) AS facturas_huerfanas FROM facturas;          -- => 1 (mala)
SELECT saldo   AS saldo_sin_descontar FROM clientes WHERE id = 1; -- => 1 (mala)
-- Factura emitida + timbre intacto = estado INCONSISTENTE.

-- ---------------------------------------------------------------------
-- 4) TU RETO
-- ---------------------------------------------------------------------
--    Haz que los dos pasos sean ATÓMICOS. Envuélvelos en una transacción
--    con manejo de error de modo que, si el segundo paso falla, el INSERT
--    también se revierta (rollback completo). En SQL puro esto se logra
--    con un bloque BEGIN ... EXCEPTION ... END (PL/pgSQL), que se
--    comporta como BEGIN/COMMIT con captura del error.
--
--    Pista: usa  DO $$ BEGIN ... EXCEPTION WHEN others THEN ... END $$;
--    Conserva la división por cero para PROBAR que, aun fallando, no
--    queda basura.
--
--    -- TODO: TU SOLUCIÓN AQUÍ
--
--    (la solución de referencia vive en soluciones/01_atomicidad.sol.sql,
--     ábrela SÓLO después de intentarlo)

-- ---------------------------------------------------------------------
-- 5) CRITERIO DE ÉXITO
-- ---------------------------------------------------------------------
--    Tras correr tu solución (que incluye el fallo simulado):
--      facturas = 0   y   saldo = 1   (rollback completo, sin huérfanas).

-- ---------------------------------------------------------------------
-- 6) CÓMO CORRER
-- ---------------------------------------------------------------------
--    ./reset.sh
--    /opt/homebrew/opt/postgresql@17/bin/psql \
--      "dbname=postgres user=postgres host=localhost" -f 01_atomicidad.sql
