#!/usr/bin/env python
# =====================================================================
# 06 — CONCURRENCIA con BLOQUEO OPTIMISTA
# =====================================================================
#
# 1) CONTEXTO
#    El MISMO choque del reto 03 y 05, pero ahora SIN candados. Apostamos
#    a que los choques son raros: cada quien lee, calcula, y al escribir
#    verifica que NADIE haya cambiado la fila mientras tanto. Si alguien
#    la cambió, reintenta. El que pierde no espera un candado: reintenta
#    y se rechaza limpio.
#
# 2) CONCEPTO
#    Bloqueo optimista = "asumo que NO vamos a chocar". Patrón:
#    leer (saldo + version) -> calcular -> UPDATE ... WHERE version = :v
#    -> revisar rowcount: si 0, alguien ganó la carrera -> REINTENTAR.
#    La columna `version` es el testigo de "nadie tocó esto".
#
# ---------------------------------------------------------------------
# 3) EL FALLO  (corre el archivo TAL CUAL: la versión naive sobre-vende)
# ---------------------------------------------------------------------
#    Sin el chequeo de version, los dos leen saldo=1 y facturan: 2
#    facturas, saldo -1.
#
# ---------------------------------------------------------------------
# 4) TU RETO
# ---------------------------------------------------------------------
#    Implementa el patrón optimista en `facturar()`:
#      1. Lee saldo Y version.
#      2. Si saldo < 1 -> rechaza.
#      3. UPDATE clientes SET saldo=saldo-1, version=version+1
#             WHERE id=1 AND version = <la version que leíste>
#      4. Si cur.rowcount == 0 -> perdiste la carrera: rollback y
#         REINTENTA (vuelve al paso 1, sin esperar candados).
#      5. Si rowcount == 1 -> inserta la factura y COMMIT.
#    Mira el bloque `# TODO:`.
#
#    (referencia en soluciones/06_optimista.sol.py)
#
# ---------------------------------------------------------------------
# 5) CRITERIO DE ÉXITO
# ---------------------------------------------------------------------
#    1 sola factura, saldo 0, version 1. El perdedor REINTENTA (no espera
#    candado) y rechaza limpio porque ya no hay saldo.
#
# ---------------------------------------------------------------------
# 6) CÓMO CORRER
# ---------------------------------------------------------------------
#    ./reset.sh
#    ~/.venvs/cli-tools/bin/python 06_optimista.py
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
    """VERSIÓN NAIVE (sin version) — sobre-vende. Hazla optimista."""
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor()

    primera_vuelta = True
    while True:
        # Leer saldo y version
        cur.execute("SELECT saldo, version FROM clientes WHERE id = 1")
        saldo, version = cur.fetchone()


        if primera_vuelta:
            barrera.wait()  # ambos leen la MISMA version la primera vez
            primera_vuelta = False

        # ============ TODO: TU SOLUCIÓN AQUÍ ============
        # Implementa: si saldo<1 -> rechaza; si no, UPDATE ... WHERE
        if saldo < 1:
            conn.rollback()
            print(f"[{nombre}] sin saldo, rechazó")
            break

        else:
            cur.execute("UPDATE clientes SET saldo = saldo - 1, version = version + 1 WHERE id = 1 AND version = %s", (version,))
            if cur.rowcount == 0:
                conn.rollback()
                print(f"[{nombre}] conflicto de version -> REINTENTA (sin candado)")
                continue

            cur.execute("INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid())")
            conn.commit()
            print(f"[{nombre}] facturó")
            break
        # version=<leída>; revisa cur.rowcount; si 0 reintenta (continue),
        # si 1 inserta factura y commit (break).
        #
        # La versión naive de abajo IGNORA `version` y por eso sobre-vende:
        if saldo >= 1:
            cur.execute("INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid())")
            cur.execute("UPDATE clientes SET saldo = saldo - 1 WHERE id = 1")
            conn.commit()
            print(f"[{nombre}] facturó")
        else:
            conn.rollback()
            print(f"[{nombre}] sin saldo, rechazó")
        break
        # ================================================
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
    if n_fact == 1 and saldo == 0 and version == 1:
        print("OK: bloqueo optimista -> 1 factura, saldo 0, version 1.")
    else:
        print("BUG: sobre-venta (esperado con la versión naive sin version-check).")


if __name__ == "__main__":
    main()
