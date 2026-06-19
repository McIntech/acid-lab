# acid-lab — aprende ACID resolviéndolo TÚ

Un laboratorio para **entender ACID a punta de chingadazos**: cada concepto es un
archivo-reto con código **roto** que corres y ves fallar con tus propios ojos. Luego
**tú** escribes la solución a mano, en tu Neovim, sin IA. Las respuestas de referencia
están en `soluciones/` para que te autocorrijas **después** de intentarlo.

Dominio: un **sistema de facturación SAT** (México). Un **timbre** es un crédito
prepagado; cada factura consume 1 timbre (`saldo - 1`). Cliente semilla: *Contador
Pérez*, RFC `PERP800101AAA`, `saldo = 1`.

## Filosofía

- Lo resuelves **tú**, a mano. La IA no te lo escribe.
- Primero **ves el bug correr**. No memorizas teoría: reproduces el problema.
- Recién entonces lees la solución de referencia y comparas con la tuya.

## Requisitos y conexión

- **PostgreSQL 17** corriendo en `localhost:5432`, usuario `postgres`, base `postgres`,
  conexión local sin password (trust).
  - `psql`: `/opt/homebrew/opt/postgresql@17/bin/psql`
  - DSN: `dbname=postgres user=postgres host=localhost`
- **Python** con `psycopg2` para los retos de concurrencia:
  - Intérprete: `~/.venvs/cli-tools/bin/python`

Prueba rápida de que todo conecta:

```bash
/opt/homebrew/opt/postgresql@17/bin/psql "dbname=postgres user=postgres host=localhost" -c "select 1"
~/.venvs/cli-tools/bin/python -c "import psycopg2; print('ok')"
```

## El mapa ACID

| #  | Lección                  | Letra / estrategia        | Archivo               |
|----|--------------------------|---------------------------|-----------------------|
| 01 | Atomicidad               | **A** — todo o nada       | `01_atomicidad.sql`   |
| 02 | Consistencia             | **C** — reglas en la base | `02_consistencia.sql` |
| 03 | Aislamiento              | **I** — SERIALIZABLE      | `03_aislamiento.py`   |
| 04 | Durabilidad              | **D** — WAL / commit      | `04_durabilidad.sql`  |
| 05 | Concurrencia: pesimista  | `SELECT ... FOR UPDATE`   | `05_pesimista.py`     |
| 06 | Concurrencia: optimista  | columna `version`         | `06_optimista.py`     |

Los retos 03, 05 y 06 atacan **el mismo choque** (dos cajeros facturan el último timbre
a la vez) con tres herramientas distintas: subir el aislamiento, candado pesimista y
versión optimista.

## Flujo de trabajo (para CADA reto)

1. **Resetea** el lab a cero:
   ```bash
   ./reset.sh
   ```
2. **Abre el reto** en Neovim y léelo completo (contexto → criterio de éxito):
   ```bash
   nvim 01_atomicidad.sql
   ```
3. **Corre el código roto** y *ve el fallo* con tus ojos (cada archivo trae su comando
   exacto en la sección `CÓMO CORRER`).
4. **Escribe tu solución** en la zona marcada `-- TODO: TU SOLUCIÓN AQUÍ`
   (o `# TODO:` en Python). Comenta el bloque `EL FALLO` cuando toque.
5. **Vuelve a correr** y verifica que se cumple el **CRITERIO DE ÉXITO** del archivo.
6. **Compara** con la respuesta de referencia en `soluciones/` — sólo después de
   haberlo intentado.

## Comandos exactos

**Reset (deja el lab en cero):**
```bash
./reset.sh
```

**Correr cada reto (primero `./reset.sh`):**
```bash
# SQL
/opt/homebrew/opt/postgresql@17/bin/psql "dbname=postgres user=postgres host=localhost" -f 01_atomicidad.sql
/opt/homebrew/opt/postgresql@17/bin/psql "dbname=postgres user=postgres host=localhost" -f 02_consistencia.sql
/opt/homebrew/opt/postgresql@17/bin/psql "dbname=postgres user=postgres host=localhost" -f 04_durabilidad.sql

# Python (concurrencia)
~/.venvs/cli-tools/bin/python 03_aislamiento.py
~/.venvs/cli-tools/bin/python 05_pesimista.py
~/.venvs/cli-tools/bin/python 06_optimista.py
```

**Verificar todo (corre las soluciones de referencia y da PASS/FAIL):**
```bash
./verificar.sh
```
> El reto 04 reinicia el servidor Postgres (`brew services restart postgresql@17`) para
> probar durabilidad de verdad; `verificar.sh` espera a que vuelva.

## Comparar tu solución

`verificar.sh` corre las soluciones de `soluciones/` (te muestra el PASS de referencia).
Para checar **tu** versión: corre tu archivo-reto y confirma su `CRITERIO DE ÉXITO`, o
copia tu solución encima de la de `soluciones/` y vuelve a correr `verificar.sh`.

## Cierre: pregunta de entrevista

**"Optimista vs pesimista, ¿cuándo cada uno?"**

- **Pesimista** (`SELECT ... FOR UPDATE`): cuando los **choques son frecuentes** o
  rehacer el trabajo es **caro**. Tomas el candado antes de tocar nada; el resto espera.
  Costo: contención (los demás se forman).
- **Optimista** (columna `version`): cuando los **choques son raros** y quieres **máxima
  concurrencia**. Nadie espera candados; sólo **el perdedor** paga, y lo único que paga
  es **reintentar**. Costo: si los choques sí son frecuentes, los reintentos se vuelven
  un desperdicio.
