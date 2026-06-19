-- =====================================================================
-- schema.sql  —  ESQUEMA BASE (naive) + SEED.  TAMBIÉN ES EL RESET.
-- =====================================================================
-- Dominio: facturación SAT (México). Un "timbre" es un crédito prepagado;
-- cada factura consume 1 timbre (saldo - 1).
--
-- OJO PEDAGÓGICO: este esquema base es INTENCIONALMENTE permisivo (sin
-- CHECK, sin UNIQUE, sin FK, sin NOT NULL). Así el reto 02 (Consistencia)
-- tiene algo real que endurecer. Correr este archivo deja el lab en cero.
--
-- Correr:  ./reset.sh        (o)   psql "<DSN>" -f schema.sql
-- =====================================================================

DROP TABLE IF EXISTS facturas;
DROP TABLE IF EXISTS clientes;

CREATE TABLE clientes (
  id      SERIAL PRIMARY KEY,
  nombre  TEXT,
  rfc     TEXT,
  saldo   INT,
  version INT DEFAULT 0
);

CREATE TABLE facturas (
  id         SERIAL PRIMARY KEY,
  cliente_id INT,
  uuid       UUID,
  creada_en  TIMESTAMPTZ DEFAULT now()
);

-- Seed: un único cliente con 1 timbre disponible.
INSERT INTO clientes (nombre, rfc, saldo, version)
VALUES ('Contador Pérez', 'PERP800101AAA', 1, 0);

-- Estado inicial para confirmar el reset.
SELECT id, nombre, rfc, saldo, version FROM clientes;
