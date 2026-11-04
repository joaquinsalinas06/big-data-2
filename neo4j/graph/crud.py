GROUP = "manual"


def create_nodes(tx):
    query = """
    MERGE (u:Usuario:ManagedRecord {id:-120012,grupo:$group})
    MERGE (c:Cancion:ManagedRecord {id:'manual-track',grupo:$group})
    SET c.titulo='Canción manual'
    RETURN u.id AS usuario,c.titulo AS cancion
    """
    return dict(tx.run(query, group=GROUP).single())


def create_relationship(tx):
    query = """
    MATCH (u:Usuario:ManagedRecord {id:-120012,grupo:$group})
    MATCH (c:Cancion:ManagedRecord {id:'manual-track',grupo:$group})
    MERGE (u)-[r:ESCUCHO {lote:$group}]->(c)
    SET r.cantidad=1
    RETURN type(r) AS relacion,r.cantidad AS cantidad
    """
    return dict(tx.run(query, group=GROUP).single())


def update_properties(tx, count):
    if type(count) is not int or count < 1:
        raise ValueError("La cantidad debe ser un entero positivo")
    query = """
    MATCH (:Usuario:ManagedRecord {id:-120012,grupo:$group})
          -[r:ESCUCHO {lote:$group}]->(:Cancion:ManagedRecord {id:'manual-track',grupo:$group})
    SET r.cantidad=$count
    RETURN r.cantidad AS cantidad
    """
    return dict(tx.run(query, group=GROUP, count=count).single())


def get_listens(tx):
    query = """
    MATCH (u:Usuario:ManagedRecord {id:-120012,grupo:$group})
          -[r:ESCUCHO {lote:$group}]->(c:Cancion:ManagedRecord {id:'manual-track',grupo:$group})
    RETURN u.id AS usuario,c.titulo AS cancion,r.cantidad AS cantidad
    """
    return [dict(r) for r in tx.run(query, group=GROUP)]


def delete_relationship(tx):
    query = """
    MATCH (:Usuario:ManagedRecord {id:-120012,grupo:$group})
          -[r:ESCUCHO {lote:$group}]->(:Cancion:ManagedRecord {id:'manual-track',grupo:$group})
    DELETE r
    """
    return tx.run(query, group=GROUP).consume().counters.relationships_deleted


def delete_nodes(tx):
    query = "MATCH (n:ManagedRecord {grupo:$group}) DETACH DELETE n"
    return tx.run(query, group=GROUP).consume().counters.nodes_deleted
