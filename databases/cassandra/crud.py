import argparse
import time
from datetime import datetime, timezone

from databases.cassandra.connection import get_session
from databases.cassandra.loader import make_listen_id, month_of

DEMO_USER_ID = -1  # no existe en ListenBrainz, así la demo no toca datos reales


def insert_listen(session, user_id, listened_at, artist_name, track_name, release_name=None, recording_msid=None):
    """Crea una escucha y devuelve su listen_id."""
    listen_id = make_listen_id(user_id, int(listened_at.timestamp()), recording_msid, artist_name, track_name)
    session.execute(
        """
        INSERT INTO listens_by_user (user_id, month, listened_at, listen_id,
                                     artist_name, track_name, release_name, recording_msid)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (user_id, month_of(listened_at), listened_at, listen_id, artist_name, track_name, release_name, recording_msid),
    )
    return listen_id


def get_listen(session, user_id, listened_at, listen_id):
    """Devuelve la escucha como dict, o None si no existe."""
    return session.execute(
        """
        SELECT * FROM listens_by_user
        WHERE user_id = %s AND month = %s AND listened_at = %s AND listen_id = %s
        """,
        (user_id, month_of(listened_at), listened_at, listen_id),
    ).one()


def get_user_listens(session, user_id, month, limit=10):
    """Escuchas de un usuario en un mes ('YYYY-MM'), de la más reciente a la más antigua."""
    return list(session.execute(
        "SELECT * FROM listens_by_user WHERE user_id = %s AND month = %s LIMIT %s",
        (user_id, month, limit),
    ))


def update_listen(session, user_id, listened_at, listen_id, track_name, release_name=None):
    """Corrige los datos de la canción. Devuelve False si la escucha no existía."""
    # En Cassandra un UPDATE crea la fila si no existe, por eso se comprueba antes (sin IF EXISTS, ver README).
    if get_listen(session, user_id, listened_at, listen_id) is None:
        return False
    session.execute(
        """
        UPDATE listens_by_user SET track_name = %s, release_name = %s
        WHERE user_id = %s AND month = %s AND listened_at = %s AND listen_id = %s
        """,
        (track_name, release_name, user_id, month_of(listened_at), listened_at, listen_id),
    )
    return True


def delete_listen(session, user_id, listened_at, listen_id):
    """Borra la escucha. Devuelve False si no existía."""
    if get_listen(session, user_id, listened_at, listen_id) is None:
        return False
    session.execute(
        """
        DELETE FROM listens_by_user
        WHERE user_id = %s AND month = %s AND listened_at = %s AND listen_id = %s
        """,
        (user_id, month_of(listened_at), listened_at, listen_id),
    )
    return True


def show(row):
    if row is None:
        return "  (no existe)"
    when = row["listened_at"].strftime("%Y-%m-%d %H:%M:%S")
    return f"  {when} UTC | {row['artist_name']} - {row['track_name']} | álbum: {row['release_name']}"


def step(title, pause):
    if pause:
        input("\n[Enter para continuar] ")
    print(f"\n{title}")


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

    step("1) CREATE: INSERT INTO listens_by_user", pause)
    listen_id = insert_listen(session, user_id, listened_at, "Los Prisioneros", "Tren al sur", "Corazones")
    print(f"  listen_id generado: {listen_id}")

    step("2) READ: SELECT por la clave primaria completa", pause)
    print(show(get_listen(session, user_id, listened_at, listen_id)))

    step("3) UPDATE: corregir canción y álbum", pause)
    print(f"  actualizada: {update_listen(session, user_id, listened_at, listen_id, 'Estrechez de corazón', 'Corazones')}")
    print(show(get_listen(session, user_id, listened_at, listen_id)))

    step("4) DELETE: borrar la escucha", pause)
    print(f"  borrada: {delete_listen(session, user_id, listened_at, listen_id)}")
    print(show(get_listen(session, user_id, listened_at, listen_id)))
    print(f"  borrar otra vez -> borrada: {delete_listen(session, user_id, listened_at, listen_id)} (ya no existía)")

    if sample_user is None or month is None:
        sample_user, month = find_sample_user(session)
    if sample_user is None:
        print("\nNo hay datos cargados todavía: ejecuta primero databases.cassandra.loader")
        return
    step(f"5) READ sobre los datos cargados: últimas escuchas del usuario {sample_user} en {month}", pause)
    started = time.perf_counter()
    rows = get_user_listens(session, sample_user, month, limit=5)
    elapsed_ms = (time.perf_counter() - started) * 1000
    for row in rows:
        print(show(row))
    total = session.execute(
        "SELECT COUNT(*) AS n FROM listens_by_user WHERE user_id = %s AND month = %s",
        (sample_user, month),
    ).one()["n"]
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
