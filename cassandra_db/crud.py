"""CRUD sobre la tabla listens_by_user (una fila = una escucha).

Clave primaria: ((user_id, month), listened_at, listen_id)
  - (user_id, month) es la partición: decide en qué nodo vive la fila.
  - listened_at y listen_id ordenan las filas dentro de la partición.
month se calcula a partir de listened_at, así que para leer, actualizar o borrar una
escucha basta con user_id + listened_at + listen_id.

En Cassandra INSERT y UPDATE son "upserts": si la fila no existe, la crean. Por eso
update y delete leen primero la fila y solo escriben si existe.

No usamos IF EXISTS (transacciones ligeras): esas escrituras toman el reloj del
servidor y las normales el del cliente. Con Docker en Windows el reloj del cliente
iba unos milisegundos adelantado y el UPDATE ... IF EXISTS respondía "aplicado"
pero quedaba con un timestamp más viejo que el INSERT, así que se perdía.

El CRUD solo toca listens_by_user. Las tablas agregadas las recalcula load_listens.

Demo para la exposición: python -m cassandra_db.crud [--step]
"""
import argparse
import time
from datetime import datetime, timezone

from cassandra_db.connection import get_session
from cassandra_db.load_listens import make_listen_id, month_of

DEMO_USER_ID = -1  # no existe en ListenBrainz, así la demo no toca datos reales

KEY = "user_id = %s AND month = %s AND listened_at = %s AND listen_id = %s"
INSERT_CQL = """INSERT INTO listens_by_user (user_id, month, listened_at, listen_id,
                             artist_name, track_name, release_name, recording_msid)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
SELECT_CQL = f"SELECT * FROM listens_by_user WHERE {KEY}"
SELECT_MONTH_CQL = "SELECT * FROM listens_by_user WHERE user_id = %s AND month = %s LIMIT %s"
UPDATE_CQL = f"UPDATE listens_by_user SET track_name = %s, release_name = %s WHERE {KEY}"
DELETE_CQL = f"DELETE FROM listens_by_user WHERE {KEY}"


def listen_key(user_id, listened_at, listen_id):
    return (user_id, month_of(listened_at), listened_at, listen_id)


def insert_listen(session, user_id, listened_at, artist_name, track_name, release_name=None, recording_msid=None):
    """Crea una escucha y devuelve su listen_id."""
    timestamp = int(listened_at.timestamp())
    listen_id = make_listen_id(user_id, timestamp, recording_msid, artist_name, track_name)
    session.execute(INSERT_CQL, (*listen_key(user_id, listened_at, listen_id),
                                 artist_name, track_name, release_name, recording_msid))
    return listen_id


def get_listen(session, user_id, listened_at, listen_id):
    """Devuelve la escucha como dict, o None si no existe."""
    return session.execute(SELECT_CQL, listen_key(user_id, listened_at, listen_id)).one()


def get_user_listens(session, user_id, month, limit=10):
    """Escuchas de un usuario en un mes ('YYYY-MM'), de la más reciente a la más antigua."""
    return list(session.execute(SELECT_MONTH_CQL, (user_id, month, limit)))


def update_listen(session, user_id, listened_at, listen_id, track_name, release_name=None):
    """Corrige los datos de la canción. Devuelve False si la escucha no existía."""
    if get_listen(session, user_id, listened_at, listen_id) is None:
        return False
    session.execute(UPDATE_CQL, (track_name, release_name, *listen_key(user_id, listened_at, listen_id)))
    return True


def delete_listen(session, user_id, listened_at, listen_id):
    """Borra la escucha. Devuelve False si no existía."""
    if get_listen(session, user_id, listened_at, listen_id) is None:
        return False
    session.execute(DELETE_CQL, listen_key(user_id, listened_at, listen_id))
    return True


def show(row):
    if row is None:
        return "  (no existe)"
    when = row["listened_at"].strftime("%Y-%m-%d %H:%M:%S")
    return f"  {when} UTC | {row['artist_name']} - {row['track_name']} | álbum: {row['release_name']}"


def step(title, cql, pause):
    if pause:
        input("\n[Enter para continuar] ")
    print(f"\n{title}\n  CQL: {' '.join(cql.split())}")


def find_sample_user(session):
    """Toma algunas particiones cargadas y devuelve la de mes más reciente."""
    partitions = [
        row for row in session.execute("SELECT DISTINCT user_id, month FROM listens_by_user LIMIT 500")
        if row["user_id"] != DEMO_USER_ID
    ]
    if not partitions:
        return None, None
    latest = max(partitions, key=lambda row: row["month"])
    return latest["user_id"], latest["month"]


def run_demo(session, pause=False, sample_user=None, month=None):
    user_id = DEMO_USER_ID
    listened_at = datetime.now(timezone.utc).replace(microsecond=0)
    print(f"Escucha de prueba: user_id={user_id}, listened_at={listened_at:%Y-%m-%d %H:%M:%S} UTC")

    step("1) CREATE: insertar una escucha", INSERT_CQL, pause)
    listen_id = insert_listen(session, user_id, listened_at, "Los Prisioneros", "Tren al sur", "Corazones")
    print(f"  listen_id generado: {listen_id}")

    step("2) READ: leerla por su clave primaria completa", SELECT_CQL, pause)
    print(show(get_listen(session, user_id, listened_at, listen_id)))

    step("3) UPDATE: corregir canción y álbum", UPDATE_CQL, pause)
    print(f"  actualizada: {update_listen(session, user_id, listened_at, listen_id, 'Estrechez de corazón', 'Corazones')}")
    print(show(get_listen(session, user_id, listened_at, listen_id)))

    step("4) DELETE: borrar la escucha", DELETE_CQL, pause)
    print(f"  borrada: {delete_listen(session, user_id, listened_at, listen_id)}")
    print(show(get_listen(session, user_id, listened_at, listen_id)))
    print(f"  borrar otra vez -> borrada: {delete_listen(session, user_id, listened_at, listen_id)} (ya no existía)")

    if sample_user is None or month is None:
        sample_user, month = find_sample_user(session)
    if sample_user is None:
        print("\nNo hay datos cargados todavía: ejecuta primero cassandra_db.load_listens")
        return
    step(f"5) READ sobre los datos cargados: últimas escuchas del usuario {sample_user} en {month}",
         SELECT_MONTH_CQL, pause)
    started = time.perf_counter()
    rows = get_user_listens(session, sample_user, month, limit=5)
    elapsed_ms = (time.perf_counter() - started) * 1000
    for row in rows:
        print(show(row))
    total = session.execute("SELECT COUNT(*) AS n FROM listens_by_user WHERE user_id = %s AND month = %s",
                            (sample_user, month)).one()["n"]
    print(f"  {len(rows)} de {total:,} escuchas de esa partición, leídas en {elapsed_ms:.1f} ms")


def main():
    parser = argparse.ArgumentParser(description="Demo CRUD de Cassandra")
    parser.add_argument("--step", action="store_true", help="Pausar entre pasos (útil para el video)")
    parser.add_argument("--user-id", type=int, help="Usuario real para el paso 5 (por defecto se elige uno)")
    parser.add_argument("--month", help="Mes YYYY-MM para el paso 5, junto con --user-id")
    args = parser.parse_args()

    session = get_session()
    try:
        run_demo(session, pause=args.step, sample_user=args.user_id, month=args.month)
    finally:
        session.cluster.shutdown()


if __name__ == "__main__":
    main()
