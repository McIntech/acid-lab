-- =====================================================================
-- SOLUCIÓN 02 — CONSISTENCIA
-- =====================================================================
-- Le ponemos reglas al motor con ALTER TABLE. La seed (saldo=1, rfc
-- único, nombre no nulo) ya las cumple, así que las constraints se
-- agregan sin pelear con los datos existentes.
-- =====================================================================

ALTER TABLE clientes ALTER COLUMN nombre SET NOT NULL;
ALTER TABLE clientes ALTER COLUMN saldo  SET NOT NULL;
ALTER TABLE clientes ADD CONSTRAINT clientes_saldo_no_negativo CHECK (saldo >= 0);
ALTER TABLE clientes ADD CONSTRAINT clientes_rfc_unico         UNIQUE (rfc);
ALTER TABLE facturas ADD CONSTRAINT facturas_cliente_fk
  FOREIGN KEY (cliente_id) REFERENCES clientes(id);

-- --- Demostración: los 4 intentos ilegales son RECHAZADOS ------------
-- Cada uno va en su propio bloque para que el script no se detenga y
-- puedas ver los 4 rechazos seguidos.
DO $$ BEGIN
  INSERT INTO clientes (nombre, rfc, saldo) VALUES ('Saldo Negativo', 'AAAA010101AAA', -50);
EXCEPTION WHEN others THEN RAISE NOTICE '1) saldo<0   RECHAZADO (esperado): %', SQLERRM; END $$;

DO $$ BEGIN
  INSERT INTO clientes (nombre, rfc, saldo) VALUES ('RFC Clonado', 'PERP800101AAA', 10);
EXCEPTION WHEN others THEN RAISE NOTICE '2) rfc dup   RECHAZADO (esperado): %', SQLERRM; END $$;

DO $$ BEGIN
  INSERT INTO facturas (cliente_id, uuid) VALUES (9999, gen_random_uuid());
EXCEPTION WHEN others THEN RAISE NOTICE '3) fk mala   RECHAZADO (esperado): %', SQLERRM; END $$;

DO $$ BEGIN
  INSERT INTO clientes (nombre, rfc, saldo) VALUES (NULL, 'BBBB020202BBB', 5);
EXCEPTION WHEN others THEN RAISE NOTICE '4) nombre NULL RECHAZADO (esperado): %', SQLERRM; END $$;

-- --- Un insert LEGAL sí entra ---------------------------------------
INSERT INTO clientes (nombre, rfc, saldo) VALUES ('Cliente Legal', 'LEGA010101AAA', 10);

SELECT count(*) AS clientes_validos FROM clientes;  -- => 2 (la seed + el legal)
