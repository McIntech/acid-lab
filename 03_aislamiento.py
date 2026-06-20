#!/usr/bin/env python
# =====================================================================
# 03 — AISLAMIENTO  (la "I" de ACID)
# =====================================================================
#
# 1) CONTEXTO
#    El Contador Pérez tiene 1 timbre. Dos peticiones de facturación
#    llegan al MISMO instante (dos cajeros, doble clic, dos pestañas).
#    Ambas leen "saldo = 1", ambas creen que pueden facturar y ambas
#    facturan: salen 2 facturas y el saldo queda en -1. Vendiste un
#    timbre que no existía (oversell). Eso es un "lost update".
#
# 2) CONCEPTO
#    Aislamiento = transacciones concurrentes no se pisan; el resultado
#    debe ser como si se hubieran ejecutado una tras otra (serializable).
#
# ---------------------------------------------------------------------
# 3) EL FALLO  (corre el archivo TAL CUAL y verás el lost update)
# ---------------------------------------------------------------------
#    Dos hilos, nivel de aislamiento por defecto (READ COMMITTED). Una
#    barrera obliga a que AMBOS lean el saldo antes de que cualquiera
#    escriba: así el choque es 100% reproducible.
#
# ---------------------------------------------------------------------
# 4) TU RETO
# ---------------------------------------------------------------------
#    Sube el aislamiento a SERIALIZABLE y maneja el error de
#    serialización (SQLSTATE 40001). Con SERIALIZABLE, Postgres deja
#    pasar UNA transacción y a la otra le revienta el commit con 40001;
#    tu código debe atrapar ese error, hacer rollback y NO facturar.
#    Edita `facturar()`:  (a) pon el aislamiento en SERIALIZABLE,
#    (b) envuelve el commit en try/except SerializationFailure.
#    Mira el bloque marcado `# TODO:` más abajo.
#
#    (referencia en soluciones/03_aislamiento.sol.py)
#
# ---------------------------------------------------------------------
# 5) CRITERIO DE ÉXITO
# ---------------------------------------------------------------------
#    Con SERIALIZABLE: se emite SÓLO 1 factura, saldo termina en 0, y el
#    hilo perdedor reporta un error de serialización (40001).
#
# ---------------------------------------------------------------------
# 6) CÓMO CORRER
# ---------------------------------------------------------------------
#    ./reset.sh
#    ~/.venvs/cli-tools/bin/python 03_aislamiento.py
# =====================================================================

import threading
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_SERIALIZABLE

DSN = "dbname=postgres user=postgres host=localhost"
barrera = threading.Barrier(2)


def preparar():
    """Estado conocido: saldo=1, version=0, sin facturas. Hace el demo repetible."""
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DELETE FROM facturas")
    cur.execute("UPDATE clientes SET saldo = 1, version = 0 WHERE id = 1")
    conn.close()


def facturar(nombre):
    """VERSIÓN NAIVE (READ COMMITTED) — provoca el lost update."""
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    conn.set_isolation_level(ISOLATION_LEVEL_SERIALIZABLE)
    cur = conn.cursor()

    # ============ TODO: TU SOLUCIÓN AQUÍ ============
    # (a) Antes de leer, sube el aislamiento a SERIALIZABLE:
    #         from psycopg2.extensions import ISOLATION_LEVEL_SERIALIZABLE
    #         conn.set_isolation_level(ISOLATION_LEVEL_SERIALIZABLE)
    # (b) Más abajo, envuelve el conn.commit() en try/except y atrapa
    #         psycopg2.errors.SerializationFailure -> rollback + "perdió".
    # ================================================

    cur.execute("SELECT saldo FROM clientes WHERE id = 1")
    saldo = cur.fetchone()[0]

    barrera.wait()  # ambos hilos leyeron saldo=1 antes de escribir

    if saldo < 1:
        print("Saldo menor a 1")
        conn.rollback()
        conn.close()
        return

    try:
        cur.execute("INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid())")
        cur.execute("UPDATE clientes SET saldo = saldo - 1 WHERE id = 1")
        conn.commit()  # <- la versión SERIALIZABLE protege este commit
    except psycopg2.errors.SerializationFailure:
        conn.rollback()
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
    if n_fact == 1 and saldo == 0:
        print("OK: aislamiento correcto (1 factura, saldo 0).")
    else:
        print("BUG: lost update / oversell (esperado con la versión naive).")


if __name__ == "__main__":
    main()
