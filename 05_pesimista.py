#!/usr/bin/env python
# =====================================================================
# 05 — CONCURRENCIA con BLOQUEO PESIMISTA
# =====================================================================
#
# 1) CONTEXTO
#    Mismo choque del reto 03: dos cajeros quieren facturar el único
#    timbre del Contador Pérez al mismo tiempo. Ahora lo resolvemos a
#    nivel de aplicación con un CANDADO: el primero que llega bloquea la
#    fila del cliente; el segundo ESPERA a que se libere y, al ver que ya
#    no hay saldo, se rechaza limpio.
#
# 2) CONCEPTO
#    Bloqueo pesimista = "asumo que vamos a chocar, así que tomo el
#    candado ANTES de tocar nada". Se hace con SELECT ... FOR UPDATE:
#    bloquea la fila hasta el COMMIT/ROLLBACK; cualquier otro que la pida
#    con FOR UPDATE se forma en la fila (espera).
#
# ---------------------------------------------------------------------
# 3) EL FALLO  (corre el archivo TAL CUAL: la versión naive sobre-vende)
# ---------------------------------------------------------------------
#    Sin candado, los dos leen saldo=1 y los dos facturan: 2 facturas,
#    saldo -1. Eso es lo que vas a corregir.
#
# ---------------------------------------------------------------------
# 4) TU RETO
# ---------------------------------------------------------------------
#    En `facturar()`, cambia la lectura por una lectura CON CANDADO:
#        SELECT saldo FROM clientes WHERE id = 1 FOR UPDATE
#    El primer hilo toma el candado y factura; el segundo se queda
#    ESPERANDO en ese SELECT hasta que el primero hace COMMIT, y cuando
#    por fin lee, ve saldo=0 y se rechaza. Mira el bloque `# TODO:`.
#
#    (referencia en soluciones/05_pesimista.sol.py)
#
# ---------------------------------------------------------------------
# 5) CRITERIO DE ÉXITO
# ---------------------------------------------------------------------
#    1 sola factura, saldo 0. El segundo hilo ESPERÓ el candado y, al
#    liberarse, rechazó porque saldo=0.
#
# ---------------------------------------------------------------------
# 6) CÓMO CORRER
# ---------------------------------------------------------------------
#    ./reset.sh
#    ~/.venvs/cli-tools/bin/python 05_pesimista.py
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
    """VERSIÓN NAIVE (sin candado) — sobre-vende. Conviértela en pesimista."""
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor()

    barrera.wait()  # ambos hilos arrancan la sección crítica a la vez

    # ============ TODO: TU SOLUCIÓN AQUÍ ============
    # Cambia esta lectura por una lectura CON CANDADO (bloqueo pesimista):
    #     SELECT saldo FROM clientes WHERE id = 1 FOR UPDATE
    # Así el segundo hilo se forma y espera el candado del primero.
    cur.execute("SELECT saldo FROM clientes WHERE id = 1 FOR UPDATE")
    saldo = cur.fetchone()[0]

    if saldo >= 1:
        cur.execute("INSERT INTO facturas (cliente_id, uuid) VALUES (1, gen_random_uuid())")
        cur.execute("UPDATE clientes SET saldo = saldo - 1 WHERE id = 1")
        conn.commit()
        print(f"[{nombre}] facturó (saldo era {saldo})")
    else:
        conn.rollback()
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
    if n_fact == 1 and saldo == 0:
        print("OK: bloqueo pesimista -> 1 factura, saldo 0.")
    else:
        print("BUG: sobre-venta (esperado con la versión naive sin candado).")


if __name__ == "__main__":
    main()
