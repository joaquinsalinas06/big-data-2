"""Consultas de lectura para el dashboard.

Cada función lee una sola partición, que es la consulta para la que se diseñó su tabla.
Devuelven listas de dicts: en Streamlit basta con pd.DataFrame(rows).

Uso: python -m cassandra_db.queries [--month 2026-10]
"""
import argparse
import time

from cassandra_db.connection import get_session


def get_daily_stats(session, year):
    return list(session.execute("SELECT * FROM daily_stats WHERE year = %s", (year,)))


def get_top_artists(session, month, limit=10):
    return list(session.execute("SELECT * FROM top_artists_by_month WHERE month = %s LIMIT %s", (month, limit)))


def get_artist_history(session, artist_name):
    return list(session.execute("SELECT month, listens FROM artist_monthly_listens WHERE artist_name = %s", (artist_name,)))


def get_user_activity(session, user_id):
    return list(session.execute("SELECT day, listens FROM user_daily_listens WHERE user_id = %s", (user_id,)))


def get_load_batches(session):
    return sorted(session.execute("SELECT * FROM load_batches"), key=lambda row: row["first_line"])


def timed(function, *args):
    started = time.perf_counter()
    result = function(*args)
    return result, (time.perf_counter() - started) * 1000


def main():
    parser = argparse.ArgumentParser(description="Resumen de lo cargado en Cassandra")
    parser.add_argument("--month", help="Mes del ranking de artistas, YYYY-MM (por defecto el último con datos)")
    args = parser.parse_args()

    session = get_session()
    try:
        years = sorted(row["year"] for row in session.execute("SELECT DISTINCT year FROM daily_stats"))
        if not years:
            print("No hay datos: ejecuta primero cassandra_db.load_listens")
            return 1
        loaded = sum(row["rows_loaded"] for row in get_load_batches(session))
        all_days = list(session.execute("SELECT listens FROM daily_stats"))

        print("=== CASSANDRA: RESUMEN ===")
        print(f"Escuchas en load_batches: {loaded:,} | suma de daily_stats: {sum(r['listens'] for r in all_days):,}")
        print(f"Días con escuchas: {len(all_days):,} ({years[0]} a {years[-1]})")

        stats, ms = timed(get_daily_stats, session, years[-1])
        print(f"\nÚltimos 7 días de {years[-1]} (consulta: {ms:.0f} ms):")
        print(f"  {'día':<10} {'escuchas':>9} {'usuarios':>9} {'esc/usuario':>11} {'crecimiento':>11}")
        for row in stats[-7:]:
            growth = f"{row['growth_pct']:+.1f}%" if row["growth_pct"] is not None else "-"
            print(f"  {row['day']!s:<10} {row['listens']:>9,} {row['active_users']:>9,} "
                  f"{row['listens_per_user']:>11.1f} {growth:>11}")

        last_day = stats[-1]["day"].date()
        month = args.month or f"{last_day.year:04d}-{last_day.month:02d}"
        top, ms = timed(get_top_artists, session, month)
        print(f"\nTop 10 artistas de {month} (consulta: {ms:.0f} ms):")
        for row in top:
            print(f"  {row['rank']:>2}. {row['artist_name']:<40} {row['listens']:>8,}  {row['share_pct']:.2f}%")

        if top:
            history, ms = timed(get_artist_history, session, top[0]["artist_name"])
            print(f"\nÚltimos 6 meses de {top[0]['artist_name']} (consulta: {ms:.0f} ms):")
            for row in history[-6:]:
                print(f"  {row['month']}  {row['listens']:>8,}")
    finally:
        session.cluster.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
