def list_artists(tx, dataset, limit=5):
    query = """
    MATCH (u:Usuario)-[:ESCUCHA_ARTISTA {lote:$dataset}]->(a:Artista)
    RETURN a.nombre AS artista,count(DISTINCT u) AS oyentes
    ORDER BY oyentes DESC,artista
    LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, limit=limit)]


def get_tracks(tx, dataset, artist, limit=5):
    query = """
    MATCH (c:Cancion)-[:INTERPRETADA_POR {lote:$dataset}]->(a:Artista {nombre:$artist})
    RETURN c.id AS identificador,c.titulo AS cancion,a.nombre AS artista
    ORDER BY cancion,identificador
    LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, artist=artist, limit=limit)]


def filter_listens(tx, dataset, user, minimum=5, limit=5):
    query = """
    MATCH (:Usuario {id:$user})-[r:ESCUCHA_ARTISTA {lote:$dataset}]->(a:Artista)
    WHERE r.cantidad >= $minimum
    RETURN a.nombre AS artista,r.cantidad AS reproducciones
    ORDER BY reproducciones DESC,artista
    LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, user=user, minimum=minimum, limit=limit)]


def search_artists(tx, dataset, text, limit=5):
    query = """
    MATCH (a:Artista)
    WHERE toLower(a.nombre) CONTAINS toLower($text)
      AND EXISTS { MATCH (:Usuario)-[:ESCUCHA_ARTISTA {lote:$dataset}]->(a) }
    RETURN a.nombre AS artista
    ORDER BY artista
    LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, text=text, limit=limit)]


def count_listens(tx, dataset):
    query = """
    MATCH (u:Usuario)-[r:ESCUCHO {lote:$dataset}]->(c:Cancion)
    RETURN count(DISTINCT u) AS usuarios,count(DISTINCT c) AS canciones,
           count(r) AS relaciones,coalesce(sum(r.cantidad),0) AS escuchas
    """
    return dict(tx.run(query, dataset=dataset).single())


def recommend_artists(tx, dataset, user, limit=3):
    query = """
    MATCH (l:Lote {id:$dataset,estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis {estado:'completo'})
    MATCH (u:Usuario {id:$user})-[p:ESCUCHA_ARTISTA {lote:l.id}]->(conocido:Artista)
    MATCH (conocido)-[f:AFIN_A {analisis:an.id}]-(nuevo:Artista)
    WHERE NOT EXISTS { MATCH (u)-[:ESCUCHA_ARTISTA {lote:l.id}]->(nuevo) }
    WITH l,an,u,nuevo,sum(p.proporcion*f.jaccard) AS puntaje,
         collect({artista_conocido:conocido.nombre,jaccard:f.jaccard,
                  usuarios_comunes:f.usuarios_comunes,aporte:p.proporcion*f.jaccard}) AS evidencia
    RETURN nuevo.nombre AS artista,puntaje,evidencia
    ORDER BY puntaje DESC,artista LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, user=user, limit=limit)]


def recommend_tracks(tx, dataset, user, limit=3):
    query = """
    MATCH (l:Lote {id:$dataset,estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis {estado:'completo'})
    MATCH (u:Usuario {id:$user})-[p:ESCUCHA_ARTISTA {lote:l.id}]->(conocido:Artista)
    MATCH (conocido)-[f:AFIN_A {analisis:an.id}]-(nuevo:Artista)
    WHERE NOT EXISTS { MATCH (u)-[:ESCUCHA_ARTISTA {lote:l.id}]->(nuevo) }
    WITH l,an,u,nuevo,sum(p.proporcion*f.jaccard) AS puntaje,
         collect({artista_conocido:conocido.nombre,jaccard:f.jaccard,
                  usuarios_comunes:f.usuarios_comunes,aporte:p.proporcion*f.jaccard}) AS evidencia
    WITH l,an,u,nuevo,puntaje,evidencia ORDER BY puntaje DESC,nuevo.nombre LIMIT $limit
    MATCH (c:Cancion)-[:INTERPRETADA_POR {lote:l.id}]->(nuevo)
    WHERE NOT EXISTS { MATCH (u)-[:ESCUCHO {lote:l.id}]->(c) }
    MATCH (oyente:Usuario)-[:ESCUCHO {lote:l.id}]->(c)
    WITH nuevo,c,puntaje,evidencia,count(DISTINCT oyente) AS audiencia
    RETURN nuevo.nombre AS artista,c.id AS cancion_id,c.titulo AS cancion,audiencia,puntaje,evidencia
    ORDER BY puntaje DESC,audiencia DESC,artista,cancion_id LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, user=user, limit=limit)]


def get_communities(tx, dataset, limit=5):
    query = """
    MATCH (l:Lote {id:$dataset,estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis {estado:'completo'})
    MATCH (c:Comunidad {analisis:an.id})
    RETURN c.id AS comunidad,c.artistas AS artistas,c.audiencia AS audiencia,
           c.representantes AS representantes
    ORDER BY audiencia DESC,comunidad LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, limit=limit)]


def get_indicators(tx, dataset):
    query = """
    MATCH (l:Lote {id:$dataset,estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis {estado:'completo'})
    RETURN an.id AS analisis,an.parametros AS parametros,
     an.artistas_seleccionados AS artistas_seleccionados,an.artistas_conectados AS artistas_conectados,
     an.artistas_aislados AS artistas_aislados,an.modularidad AS modularidad,
     an.usuarios_lote AS usuarios_lote,an.usuarios_con_recomendaciones AS usuarios_con_recomendaciones,
     an.cobertura_recomendaciones AS cobertura_recomendaciones,
     an.usuarios_con_escuchas_clasificadas AS usuarios_con_escuchas_clasificadas,
     an.escuchas_clasificadas AS escuchas_clasificadas,
     an.proporcion_escuchas_clasificadas AS proporcion_escuchas_clasificadas,
     an.diversidad_media_usuarios_clasificados AS diversidad_media_usuarios_clasificados
    """
    return [dict(r) for r in tx.run(query, dataset=dataset)]


def get_bridge_artists(tx, dataset, limit=5):
    query = """
    MATCH (l:Lote {id:$dataset,estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis {estado:'completo'})
    MATCH (art:Artista)-[p:PERTENECE_A {analisis:an.id}]->(c:Comunidad)
    RETURN art.nombre AS artista,p.puente AS coeficiente_puente,c.id AS comunidad
    ORDER BY coeficiente_puente DESC,artista LIMIT $limit
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, limit=limit)]


def get_user_diversity(tx, dataset, user):
    query = """
    MATCH (l:Lote {id:$dataset,estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis {estado:'completo'})
    MATCH (u:Usuario {id:$user})
    OPTIONAL MATCH (u)-[r:ESCUCHA_ARTISTA {lote:l.id}]->(:Artista)-[:PERTENECE_A {analisis:an.id}]->(c:Comunidad)
    WITH u,c,sum(r.cantidad) AS cantidad
    WITH u,collect(CASE WHEN c IS NOT NULL THEN {comunidad:c.id,cantidad:cantidad} END) AS reparto
    WITH u,reparto,reduce(total=0,x IN reparto|total+x.cantidad) AS total
    RETURN u.id AS usuario_id,reparto,total AS escuchas_clasificadas,
     CASE WHEN size(reparto)=0 THEN null WHEN size(reparto)=1 THEN 0.0
     ELSE -reduce(entropia=0.0,x IN reparto|
       entropia+(1.0*x.cantidad/total)*log(1.0*x.cantidad/total))/log(size(reparto)) END AS diversidad
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, user=user)]


def find_artist_path(tx, dataset, artist, destination):
    query = """
    MATCH (l:Lote {id:$dataset,estado:'completo'})-[:ANALISIS_ACTIVO]->(an:Analisis {estado:'completo'})
    MATCH (a:Artista {nombre:$artist}),(b:Artista {nombre:$target})
    WHERE a<>b
    MATCH camino=shortestPath((a)-[:AFIN_A*1..6]-(b))
    WHERE all(r IN relationships(camino) WHERE r.analisis=an.id)
    RETURN [n IN nodes(camino)|n.nombre] AS artistas,length(camino) AS saltos
    LIMIT 1
    """
    return [dict(r) for r in tx.run(query, dataset=dataset, artist=artist, target=destination)]
