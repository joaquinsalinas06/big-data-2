-- Modelo de Cassandra para Music DNA.
-- Cada tabla responde a una consulta concreta (query-first), por eso hay datos repetidos entre tablas.
-- SimpleStrategy con RF=1 porque en desarrollo corremos un solo nodo.

CREATE KEYSPACE IF NOT EXISTS music_dna
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Q1: historial de escuchas de un usuario en un mes, de la más reciente a la más antigua.
-- Particionar por (usuario, mes) evita que un usuario muy activo genere una partición enorme.
CREATE TABLE IF NOT EXISTS music_dna.listens_by_user (
    user_id        bigint,
    month          text,
    listened_at    timestamp,
    listen_id      uuid,
    artist_name    text,
    track_name     text,
    release_name   text,
    recording_msid text,
    PRIMARY KEY ((user_id, month), listened_at, listen_id)
) WITH CLUSTERING ORDER BY (listened_at DESC, listen_id ASC);

-- Q2: serie diaria de un año con los KPIs de cada día.
CREATE TABLE IF NOT EXISTS music_dna.daily_stats (
    year             int,
    day              date,
    listens          bigint,
    active_users     int,
    listens_per_user double,
    growth_pct       double,
    PRIMARY KEY ((year), day)
);

-- Q3: artistas más escuchados de un mes, ya ordenados por rank
-- (Cassandra solo ordena por las columnas de clustering).
CREATE TABLE IF NOT EXISTS music_dna.top_artists_by_month (
    month       text,
    rank        int,
    artist_name text,
    listens     bigint,
    share_pct   double,
    PRIMARY KEY ((month), rank)
);

-- Q4: evolución mes a mes de un artista.
CREATE TABLE IF NOT EXISTS music_dna.artist_monthly_listens (
    artist_name text,
    month       text,
    listens     bigint,
    PRIMARY KEY ((artist_name), month)
);

-- Q5: actividad diaria de un usuario.
CREATE TABLE IF NOT EXISTS music_dna.user_daily_listens (
    user_id bigint,
    day     date,
    listens int,
    PRIMARY KEY ((user_id), day)
);

-- Lotes del archivo ya escritos en listens_by_user.
CREATE TABLE IF NOT EXISTS music_dna.load_batches (
    batch_id     text PRIMARY KEY,
    source_file  text,
    first_line   bigint,
    last_line    bigint,
    rows_loaded  bigint,
    rows_skipped bigint,
    duplicates   bigint,
    loaded_at    timestamp
);
