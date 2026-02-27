"""
src/extraccion_subgrafos/utils_interactions.py
Consultas a la base de datos Neo4j 'interactions'.
"""
import sys
from pathlib import Path

# Añadir src/ al path para importar config
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

from py2neo import Graph


def get_interactions_graph():
    """Conecta a la base 'interactions' en Neo4j."""
    return Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), name="interactions")


def get_user_interacted_hotels(user_id: int):
    """
    Devuelve la lista de IDs de hoteles con los que el usuario ha interactuado.
    """
    graph = get_interactions_graph()
    query = """
    MATCH (u:User {id: $user_id})-[:RATED]->(b:Business)
    RETURN b.id AS hotel_id
    """
    result = graph.run(query, user_id=user_id).data()
    return [r['hotel_id'] for r in result]