#!/usr/bin/env python
# =====================================================================
# SOLUCIÓN 05 — BLOQUEO PESIMISTA (SELECT ... FOR UPDATE)
# =====================================================================
# El primer hilo toma el candado de la fila del cliente con FOR UPDATE,
# factura y hace COMMIT (libera el candado). El segundo hilo se quedó
# BLOQUEADO en su propio FOR UPDATE; al liberarse, lee el saldo YA
# actualizado (0) y se rechaza. Resultado: 1 factura, saldo 0.
# =====================================================================

import threading
import psycopg2

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
    conn.autocommit = False
    cur = conn.cursor()

    barrera.wait()  # ambos pelean por el candado al mismo tiempo

    # Lectura CON CANDADO: el 2.º hilo se forma aquí hasta el COMMIT del 1.º.
    cur.execute("SELECT saldo FROM clientes WHERE id = 1 FOR UPDATE")
    saldo = cur.fetchone()[0]

    if saldo >= 1:
        cur.execute("INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid())")
        cur.execute("UPDATE clientes SET saldo = saldo - 1 WHERE id = 1")
        conn.commit()  # libera el candado
        print(f"[{nombre}] facturó (saldo era {saldo})")
    else:
        conn.rollback()  # libera el candado
        print(f"[{nombre}] esperó el candado y rechazó: saldo={saldo}")
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
    assert n_fact == 1 and saldo == 0, "FALLO: el candado debió dejar 1 factura y saldo 0"
    print("OK: bloqueo pesimista -> 1 factura, saldo 0.")


if __name__ == "__main__":
    main()
