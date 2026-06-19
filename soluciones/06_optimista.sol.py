#!/usr/bin/env python
# =====================================================================
# SOLUCIÓN 06 — BLOQUEO OPTIMISTA (columna version)
# =====================================================================
# Nadie toma candados. Cada hilo lee (saldo, version) y al escribir exige
# WHERE version = <la que leyó>. El primero que confirma sube version 0->1.
# El segundo intenta UPDATE ... WHERE version=0, pero ya vale 1, así que
# rowcount=0: perdió la carrera, hace rollback y REINTENTA. En el reintento
# lee saldo=0 y se rechaza limpio. Resultado: 1 factura, saldo 0, version 1.
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

    primera_vuelta = True
    intentos = 0
    while True:
        intentos += 1
        cur.execute("SELECT saldo, version FROM clientes WHERE id = 1")
        saldo, version = cur.fetchone()

        if primera_vuelta:
            barrera.wait()  # ambos leen version=0 antes de competir
            primera_vuelta = False

        if saldo < 1:
            conn.rollback()
            print(f"[{nombre}] sin saldo, rechazó (intentos={intentos})")
            break

        # UPDATE condicionado a que NADIE haya tocado la fila (version intacta).
        cur.execute(
            "UPDATE clientes SET saldo = saldo - 1, version = version + 1 "
            "WHERE id = 1 AND version = %s",
            (version,),
        )
        if cur.rowcount == 0:
            # Otro hilo ganó: la version cambió bajo nuestros pies. Reintenta.
            conn.rollback()
            print(f"[{nombre}] conflicto de version -> REINTENTA (sin candado)")
            continue

        cur.execute("INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid())")
        conn.commit()
        print(f"[{nombre}] facturó (intentos={intentos})")
        break
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
    cur.execute("SELECT saldo, version FROM clientes WHERE id = 1")
    saldo, version = cur.fetchone()
    conn.close()

    print(f"\nRESULTADO: facturas={n_fact}  saldo={saldo}  version={version}")
    assert n_fact == 1 and saldo == 0 and version == 1, \
        "FALLO: optimista debió dejar 1 factura, saldo 0, version 1"
    print("OK: bloqueo optimista -> 1 factura, saldo 0, version 1.")


if __name__ == "__main__":
    main()
