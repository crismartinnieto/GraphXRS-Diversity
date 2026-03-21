"""
src/extraccion_subgrafos/subgrafo_conocimiento/utils_knowledge.py
Consultas a la base de datos Neo4j 'knowledge'.
"""
import os
from py2neo import Graph

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test12345")


def get_knowledge_graph():
    return Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), name="knowledge")


def get_subgraph_for_hotels(hotel_ids):
    """
    Devuelve nodos y relaciones del subgrafo de conocimiento
    directamente conectado a cada hotel.
    """
    graph = get_knowledge_graph()
    hotel_ids = [str(h) for h in hotel_ids]

    query = """
    MATCH (h:Business {id: $hotel_id})-[r]-(n)
    RETURN h, r, n
    """

    nodes = {}
    rels  = []

    for h in hotel_ids:
        results = list(graph.run(query, hotel_id=h))
        print(f"  [KG-QUERY] hotel_id='{h}' (str) → {len(results)} registros")
        
        if len(results) == 0:
            results = list(graph.run(query, hotel_id=int(h)))
            print(f"  [KG-QUERY] hotel_id={int(h)} (int) → {len(results)} registros")

        for record in results:
            hnode = record["h"]
            rel   = record["r"]
            nnode = record["n"]

            h_id = str(hnode.identity)
            n_id = str(nnode.identity)

            if h_id not in nodes:
                nodes[h_id] = {"id": h_id, "labels": list(hnode.labels), "properties": dict(hnode)}
            if n_id not in nodes:
                nodes[n_id] = {"id": n_id, "labels": list(nnode.labels), "properties": dict(nnode)}

            rels.append({
                "id":            str(rel.identity),
                "type":          type(rel).__name__,
                "start_node_id": h_id,
                "end_node_id":   n_id,
                "properties":    dict(rel)
            })

    return list(nodes.values()), rels