#!/usr/bin/env python
# =====================================================================
# 07 — IDEMPOTENCIA  (el doble clic del MISMO usuario)
# =====================================================================
#
# 1) CONTEXTO
#    Distinto a los retos 03/05/06. Aquí NO son dos cajeros peleando por
#    el ultimo timbre: es UN SOLO usuario que da clic en "Timbrar", la
#    pantalla se queda pensando, y vuelve a dar clic. Su navegador manda
#    la MISMA peticion dos veces. Resultado naive: 2 facturas identicas
#    para algo que el usuario pidio UNA vez. (Sobra saldo; el problema
#    NO es concurrencia de inventario, es la peticion repetida.)
#
# 2) CONCEPTO
#    Idempotencia = ejecutar la misma operacion N veces produce el MISMO
#    efecto que ejecutarla 1 vez. El truco: el cliente manda una
#    "idempotency_key" UNICA por intento (la misma en ambos clicks). El
#    servidor procesa el primero; el segundo, con la misma llave, NO
#    repite — devuelve el resultado anterior. La llave vive en la BASE
#    como columna UNIQUE, y ON CONFLICT hace el "revisar y marcar" en un
#    solo paso atomico (imposible de partir, incluso si llegan a la vez).
#
# ---------------------------------------------------------------------
# 3) EL FALLO  (corre el archivo TAL CUAL: la version naive duplica)
# ---------------------------------------------------------------------
#    La version naive ignora la idempotency_key e inserta siempre.
#    Dos clicks = 2 facturas para el mismo intento.
#
# ---------------------------------------------------------------------
# 4) TU RETO
# ---------------------------------------------------------------------
#    En `facturar()`, haz la insercion IDEMPOTENTE:
#      1. Incluye la idempotency_key en el INSERT.
#      2. Usa  ... ON CONFLICT (idempotency_key) DO NOTHING
#      3. Revisa cur.rowcount:
#           - rowcount == 1 -> es la primera vez: factura creada, COMMIT.
#           - rowcount == 0 -> llave repetida: NO crees otra. Es un
#             duplicado -> trata como exito idempotente (commit/rollback
#             + mensaje "duplicado ignorado"), NO insertes de nuevo.
#    Mira el bloque `# TODO:`.
#
#    Pista: la columna `idempotency_key` (TEXT UNIQUE) ya la crea
#    `preparar()`. Tu trabajo es USARLA.
#
#    (referencia en soluciones/07_idempotencia.sol.py)
#
# ---------------------------------------------------------------------
# 5) CRITERIO DE ÉXITO
# ---------------------------------------------------------------------
#    1 sola factura, aunque se mando el MISMO intento dos veces. El
#    segundo click se reconoce como duplicado y no crea nada.
#
# ---------------------------------------------------------------------
# 6) CÓMO CORRER
# ---------------------------------------------------------------------
#    ./reset.sh
#    ~/.venvs/cli-tools/bin/python 07_idempotencia.py
# =====================================================================

import threading
import psycopg2

DSN = "dbname=postgres user=postgres host=localhost"
barrera = threading.Barrier(2)

# Misma llave en ambos clicks: es el MISMO intento de pago del usuario.
LLAVE_DEL_INTENTO = "intento-pago-2026-0001"


def preparar():
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("DELETE FROM facturas")
    # Saldo de sobra: aqui el problema NO es el inventario, es el duplicado.
    cur.execute("UPDATE clientes SET saldo = 5, version = 0 WHERE id = 1")
    # La idempotency_key vive en la BASE como columna UNIQUE.
    cur.execute("ALTER TABLE facturas ADD COLUMN IF NOT EXISTS idempotency_key TEXT UNIQUE")
    conn.close()


def facturar(nombre, idem_key):
    """VERSIÓN NAIVE: ignora la llave e inserta siempre. Hazla idempotente."""
    conn = psycopg2.connect(DSN)
    conn.autocommit = False
    cur = conn.cursor()
    barrera.wait()  # los dos clicks llegan casi al mismo tiempo

    # ============ TODO: TU SOLUCIÓN AQUÍ ============
    # Haz este INSERT idempotente con la idempotency_key + ON CONFLICT,
    # y decide segun cur.rowcount (1 = creada, 0 = duplicado ignorado).
    #
    # La version naive de abajo NO usa la llave -> duplica:

    cur.execute("INSERT INTO facturas (cliente_id, uuid, idempotency_key) " 
                "VALUES (1, gen_random_uuid(), %s) "
                "ON CONFLICT (idempotency_key) DO NOTHING", (idem_key,))

    conn.commit()
    print(f"[{nombre}] facturó")
    print(cur.rowcount)
    # ================================================
    conn.close()


def main():
    preparar()
    # Mismo usuario, mismo intento, MISMA llave -> dos clicks.
    hilos = [
        threading.Thread(target=facturar, args=(n, LLAVE_DEL_INTENTO))
        for n in ("click-1", "click-2")
    ]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM facturas")
    n_fact = cur.fetchone()[0]
    conn.close()

    print(f"\nRESULTADO: facturas={n_fact}  (se mando el MISMO intento 2 veces)")
    if n_fact == 1:
        print("OK: idempotencia -> 1 intento = 1 factura, sin importar los clicks.")
    else:
        print("BUG: duplicado (esperado con la version naive que ignora la llave).")


if __name__ == "__main__":
    main()
