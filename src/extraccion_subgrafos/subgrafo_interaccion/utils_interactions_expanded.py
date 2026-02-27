"""
src/extraccion_subgrafos/subgrafo_interaccion/utils_interactions_expanded.py
Consultas al grafo 'expanded-recommendations' en Neo4j.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

from py2neo import Graph


def get_expanded_graph():
    return Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), name="expanded-recommendations")


def get_user_interacted_hotels(user_id: int):
    """Hoteles históricos del usuario (rating > 0)."""
    graph = get_expanded_graph()
    query = """
    MATCH (u:User {id: $user_id})-[r:RATED]->(b:Business)
    WHERE r.rating > 0.0
    RETURN b.id AS hotel_id, r.rating AS rating
    """
    result = graph.run(query, user_id=user_id).data()
    return [(r['hotel_id'], r['rating']) for r in result]


def get_user_recommended_hotels(user_id: int):
    """Hoteles recomendados al usuario (rating = 10.0)."""
    graph = get_expanded_graph()
    query = """
    MATCH (u:User {id: $user_id})-[r:RATED]->(b:Business)
    WHERE r.rating = 10.0
    RETURN b.id AS hotel_id
    """
    result = graph.run(query, user_id=user_id).data()
    return [r['hotel_id'] for r in result]