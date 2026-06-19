-- =====================================================================
-- 02 — CONSISTENCIA  (la "C" de ACID)
-- =====================================================================
--
-- 1) CONTEXTO
--    La base de facturación debe RECHAZAR por sí sola los datos ilegales:
--    saldos negativos (timbres que no existen), RFC duplicados (dos
--    clientes con el mismo RFC), facturas que apuntan a un cliente que no
--    existe, y campos obligatorios en NULL. Si la app es el único guardián,
--    tarde o temprano entra basura.
--
-- 2) CONCEPTO
--    Consistencia = la base sólo transita de un estado VÁLIDO a otro
--    estado VÁLIDO; las REGLAS (constraints) las hace cumplir el motor,
--    no la confianza en el programador.
--
-- ---------------------------------------------------------------------
-- 3) EL FALLO  (corre el archivo TAL CUAL y verás que TODO pasa)
-- ---------------------------------------------------------------------
-- El esquema base no tiene constraints, así que estas 4 aberraciones
-- entran sin chistar:
--
--    ▼▼▼ EL FALLO — comenta este bloque cuando vayas a resolver ▼▼▼
-- INSERT INTO clientes (nombre, rfc, saldo) VALUES ('Saldo Negativo', 'AAAA010101AAA', -50);     -- saldo < 0
-- INSERT INTO clientes (nombre, rfc, saldo) VALUES ('RFC Clonado',    'PERP800101AAA', 10);      -- rfc duplicado
-- INSERT INTO facturas (cliente_id, uuid)   VALUES (9999, gen_random_uuid());                    -- cliente inexistente
-- INSERT INTO clientes (nombre, rfc, saldo) VALUES (NULL, 'BBBB020202BBB', 5);                   -- nombre NULL
--    ▲▲▲ FIN EL FALLO ▲▲▲
--
SELECT 'basura aceptada' AS estado, count(*) AS filas FROM clientes; -- crece de más

-- ---------------------------------------------------------------------
-- 4) TU RETO
-- ---------------------------------------------------------------------
--    Endurece el esquema con constraints para que la BASE rechace lo
--    ilegal. Necesitas, como mínimo:
--      - CHECK (saldo >= 0)            en clientes
--      - UNIQUE (rfc)                  en clientes
--      - NOT NULL en nombre y saldo    en clientes
--      - FOREIGN KEY (cliente_id)      en facturas -> clientes(id)
--    Usa ALTER TABLE ... ADD CONSTRAINT / ALTER COLUMN ... SET NOT NULL.
--    Luego DEMUESTRA que los 4 inserts ilegales fallan y uno legal pasa.
--
--    -- TODO: TU SOLUCIÓN AQUÍ
ALTER TABLE clientes
  ALTER COLUMN nombre SET NOT NULL,
  ALTER COLUMN saldo SET NOT NULL,
  ADD CONSTRAINT rfc_unico UNIQUE (rfc),
  ADD CONSTRAINT saldo_no_neg CHECK (saldo >= 0);

ALTER TABLE facturas
  ALTER COLUMN cliente_id SET NOT NULL,
  ADD CONSTRAINT cliente_id_fk FOREIGN KEY (cliente_id) REFERENCES clientes(id);


DO $$ 
  BEGIN
    INSERT INTO clientes (nombre, rfc, saldo) VALUES ('Saldo Negativo', 'AAAA010101AAA', -50);     -- saldo < 0
    EXCEPTION WHEN others THEN RAISE NOTICE 'VALOR NEGATIVO RECHAZADO: %', SQLERRM;
  END $$;

DO $$ 
  BEGIN
    INSERT INTO clientes (nombre, rfc, saldo) VALUES ('RFC Clonado',    'PERP800101AAA', 10);      -- rfc duplicado
    EXCEPTION WHEN others THEN RAISE NOTICE 'RFC DUPLICADO RECHAZADO: %', SQLERRM;
  END $$;

DO $$ 
  BEGIN
    INSERT INTO facturas (cliente_id, uuid)   VALUES (9999, gen_random_uuid());                    -- cliente inexistente
    EXCEPTION WHEN others THEN RAISE NOTICE 'CLIENTE INEXISTENTE RECHAZADO: %', SQLERRM;
  END $$;

DO $$ 
  BEGIN
    INSERT INTO clientes (nombre, rfc, saldo) VALUES (NULL, 'BBBB020202BBB', 5);                   -- nombre NULL
    EXCEPTION WHEN others THEN RAISE NOTICE 'NOMBRE NULL RECHAZADO: %', SQLERRM;
  END $$;

-- Probamos uno legal.
INSERT INTO clientes (nombre, rfc, saldo) VALUES ('Franco Limon', 'HHBB020202BBB', 1);                   -- nombre NULL
--
--    (referencia en soluciones/02_consistencia.sol.sql)
-- EXTRA LOGS:

--      estado      | filas
-- -----------------+-------
--  basura aceptada |     1
-- (1 row)
--
-- ALTER TABLE
-- ALTER TABLE
-- psql:02_consistencia.sql:60: NOTICE:  VALOR NEGATIVO RECHAZADO: new row for relation "clientes" violates check constraint "saldo_no_neg"
-- DO
-- psql:02_consistencia.sql:66: NOTICE:  RFC DUPLICADO RECHAZADO: duplicate key value violates unique constraint "rfc_unico"
-- DO
-- psql:02_consistencia.sql:72: NOTICE:  CLIENTE INEXISTENTE RECHAZADO: insert or update on table "facturas" violates foreign key constraint "cliente_id_fk"
-- DO
-- psql:02_consistencia.sql:78: NOTICE:  NOMBRE NULL RECHAZADO: null value in column "nombre" of relation "clientes" violates not-null constraint
-- DO
-- INSERT 0 1

-- ---------------------------------------------------------------------
-- 5) CRITERIO DE ÉXITO
-- ---------------------------------------------------------------------
--    Con las constraints puestas: los 4 intentos ilegales son RECHAZADOS
--    por el motor y un INSERT legal entra sin problema.

-- ---------------------------------------------------------------------
-- 6) CÓMO CORRER
-- ---------------------------------------------------------------------
--    ./reset.sh
--    /opt/homebrew/opt/postgresql@17/bin/psql \
--      "dbname=postgres user=postgres host=localhost" -f 02_consistencia.sql
