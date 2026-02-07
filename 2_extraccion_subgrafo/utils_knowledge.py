from py2neo import Graph

def get_knowledge_graph(uri = "bolt://localhost:7687", user="neo4j", password="test12345"):
    """
    Conecta al grafo de conocimiento.
    """
    return Graph(uri, name="knowledge", auth=(user, password))


def get_related_nodes_for_hotels(hotel_ids):
    """
    Devuelve todos los nodos del grafo de conocimiento conectados
    a un listado de hoteles.
    """
    graph = get_knowledge_graph()

    query = """
    MATCH (h:Business)-[r]-(n)
    WHERE h.id IN $hotel_ids
    RETURN DISTINCT h.id AS hotel_id, type(r) AS relation, 
                    n.id AS related_id, labels(n) AS labels
    """

    result = graph.run(query, hotel_ids=hotel_ids).data()
    return result


def get_subgraph_for_hotels(hotel_ids):
    """
    Devuelve nodos y relaciones del subgrafo de conocimiento
    directamente conectado a cada hotel, usando IDs únicos
    para cada nodo y referencias correctas en las relaciones.
    """
    graph = get_knowledge_graph()
    hotel_ids = [str(h) for h in hotel_ids]

    query = """
    MATCH (h:Business {id: $hotel_id})-[r]-(n)
    RETURN h, r, n
    """

    nodes = {}
    rels = []

    for h in hotel_ids:
        result = graph.run(query, hotel_id=h)
        for record in result:
            hnode = record["h"]
            rel = record["r"]
            nnode = record["n"]

            # Usar el identity de Neo4j como ID único
            h_id = str(hnode.identity)
            n_id = str(nnode.identity)

            # Guardar nodos (si no existen ya)
            if h_id not in nodes:
                nodes[h_id] = {
                    "id": h_id,
                    "labels": list(hnode.labels),
                    "properties": dict(hnode)
                }
            if n_id not in nodes:
                nodes[n_id] = {
                    "id": n_id,
                    "labels": list(nnode.labels),
                    "properties": dict(nnode)
                }

            # Guardar relación apuntando a los IDs únicos
            rels.append({
                "id": str(rel.identity),
                "type": rel.__class__.__name__,  # o rel.type si usas py2neo
                "start_node_id": h_id,
                "end_node_id": n_id,
                "properties": dict(rel)
            })

    return list(nodes.values()), rels

