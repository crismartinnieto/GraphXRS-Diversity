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
    Devuelve nodos y relaciones del subgrafo de conocimiento que contiene a esos hoteles.
    """
    graph = get_knowledge_graph()

    # Asegurarse de que todos los IDs sean strings 
    hotel_ids = [str(h) for h in hotel_ids]

    query = """
    MATCH path = (h:Business)-[*1..2]-(n)
    WHERE h.id IN $hotel_ids
    RETURN DISTINCT path
    """

    result = graph.run(query, hotel_ids=hotel_ids)

    nodes = set()
    rels = set()

    for record in result:
        path = record["path"]
        for node in path.nodes:
            nodes.add(node)
        for rel in path.relationships:
            rels.add(rel)

    return list(nodes), list(rels)
