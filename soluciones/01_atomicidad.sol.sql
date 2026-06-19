-- =====================================================================
-- SOLUCIÓN 01 — ATOMICIDAD
-- =====================================================================
-- Un bloque DO de PL/pgSQL corre dentro de UNA sola transacción. El
-- BEGIN ... EXCEPTION establece un savepoint implícito: si algo lanza
-- excepción, PostgreSQL revierte TODO lo hecho dentro del bloque.
-- Es el equivalente en SQL puro a:  try { commit } catch { rollback }.
-- =====================================================================

DO $$
BEGIN
  -- Paso 1: la factura.
  INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid());
  -- Paso 2: descontar el timbre. Forzamos el fallo a mitad (1/0).
  UPDATE clientes SET saldo = saldo - (1 / 0) WHERE id = 1;
  -- Si llegáramos aquí sin error, el bloque confirma ambos pasos.
EXCEPTION WHEN others THEN
  -- El fallo se atrapa: el bloque ya revirtió el INSERT y el UPDATE.
  RAISE NOTICE 'Fallo a mitad atrapado -> rollback completo (%).', SQLERRM;
END $$;

-- Comprobación: nada quedó a medias.
SELECT count(*) AS facturas FROM facturas;            -- => 0
SELECT saldo   AS saldo    FROM clientes WHERE id = 1; -- => 1

-- -- Variante "camino feliz" (sin el 1/0): ambos pasos se confirman
-- -- juntos y entonces facturas = 1, saldo = 0.
-- DO $$
-- BEGIN
--   INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid());
--   UPDATE clientes SET saldo = saldo - 1 WHERE id = 1;
-- EXCEPTION WHEN others THEN
--   RAISE NOTICE 'rollback: %', SQLERRM;
-- END $$;
