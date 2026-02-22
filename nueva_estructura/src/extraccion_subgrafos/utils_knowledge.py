"""
src/extraccion_subgrafos/utils_knowledge.py
Consultas a la base de datos Neo4j 'knowledge'.
"""
import sys
from pathlib import Path

# Añadir src/ al path para importar config
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

from py2neo import Graph


def get_knowledge_graph():
    """Conecta a la base 'knowledge' en Neo4j."""
    return Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), name="knowledge")


def get_subgraph_for_hotels(hotel_ids):
    """
    Devuelve nodos y relaciones del subgrafo de conocimiento
    directamente conectado a cada hotel.
    Usa el identity de Neo4j como ID único para evitar colisiones.
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
            rel   = record["r"]
            nnode = record["n"]

            h_id = str(hnode.identity)
            n_id = str(nnode.identity)

            if h_id not in nodes:
                nodes[h_id] = {
                    "id":         h_id,
                    "labels":     list(hnode.labels),
                    "properties": dict(hnode)
                }
            if n_id not in nodes:
                nodes[n_id] = {
                    "id":         n_id,
                    "labels":     list(nnode.labels),
                    "properties": dict(nnode)
                }

            rels.append({
                "id":           str(rel.identity),
                "type":         type(rel).__name__,
                "start_node_id": h_id,
                "end_node_id":   n_id,
                "properties":   dict(rel)
            })

    return list(nodes.values()), rels