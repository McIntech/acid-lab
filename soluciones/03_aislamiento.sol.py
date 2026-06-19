#!/usr/bin/env python
# =====================================================================
# SOLUCIÓN 03 — AISLAMIENTO con SERIALIZABLE
# =====================================================================
# Cada transacción corre en SERIALIZABLE. Postgres usa SSI: detecta que
# las dos transacciones leyeron y escribieron la misma fila de forma
# incompatible y aborta a UNA con SQLSTATE 40001. Esa la atrapamos,
# hacemos rollback y NO facturamos. Resultado: 1 factura, saldo 0.
# =====================================================================

import threading
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_SERIALIZABLE

DSN = "dbname=postgres user=postgres host=localhost"
barrera = threading.Barrier(2)


def preparar():
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DELETE FROM facturas")
    cur.execute("UPDATE clientes SET saldo = 1, version = 0 WHERE id = 1")
    conn.close()


def facturar(nombre):
    conn = psycopg2.connect(DSN)
    conn.set_isolation_level(ISOLATION_LEVEL_SERIALIZABLE)  # (a) SERIALIZABLE
    cur = conn.cursor()

    cur.execute("SELECT saldo FROM clientes WHERE id = 1")
    saldo = cur.fetchone()[0]

    barrera.wait()  # forzar que ambos lean saldo=1 -> garantiza el conflicto

    if saldo < 1:
        conn.rollback()
        print(f"[{nombre}] sin saldo, no facturó")
        conn.close()
        return

    try:
        cur.execute("INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid())")
        cur.execute("UPDATE clientes SET saldo = saldo - 1 WHERE id = 1")
        conn.commit()  # (b) aquí puede saltar 40001
        print(f"[{nombre}] facturó")
    except psycopg2.errors.SerializationFailure:
        conn.rollback()  # revierte INSERT + UPDATE: este hilo NO factura
        print(f"[{nombre}] error de serialización (40001) -> rollback, no facturó")
    finally:
        conn.close()


def main():
    preparar()
    hilos = [threading.Thread(target=facturar, args=(n,)) for n in ("cajero-A", "cajero-B")]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM facturas")
    n_fact = cur.fetchone()[0]
    cur.execute("SELECT saldo FROM clientes WHERE id = 1")
    saldo = cur.fetchone()[0]
    conn.close()

    print(f"\nRESULTADO: facturas={n_fact}  saldo={saldo}")
    assert n_fact == 1 and saldo == 0, "FALLO: SERIALIZABLE debió dejar 1 factura y saldo 0"
    print("OK: SERIALIZABLE -> 1 factura, saldo 0.")


if __name__ == "__main__":
    main()
