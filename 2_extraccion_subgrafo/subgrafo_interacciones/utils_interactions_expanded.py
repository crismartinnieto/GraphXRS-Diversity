from py2neo import Graph
import os

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "test12345")

def get_expanded_graph():
    """Conecta al grafo expandido de interacciones"""
    return Graph(uri, auth=(user, password), name="expanded-recommendations")


def get_user_interacted_hotels(user_id: int):
    """
    Devuelve los hoteles con los que el usuario ha interactuado
    (históricos, rating != 1.0)
    """
    graph = get_expanded_graph()
    query = """
    MATCH (u:User {id: $user_id})-[r:RATED]->(b:Business)
    WHERE r.rating > 0.0
    RETURN b.id AS hotel_id, r.rating AS rating
    """
    result = graph.run(query, user_id=user_id).data()
    return [(r['hotel_id'], r['rating']) for r in result]


def get_user_recommended_hotels(user_id: int):
    """
    Devuelve los hoteles recomendados al usuario
    (rating = 1.0)
    """
    graph = get_expanded_graph()
    query = """
    MATCH (u:User {id: $user_id})-[r:RATED]->(b:Business)
    WHERE r.rating = 10.0
    RETURN b.id AS hotel_id
    """
    result = graph.run(query, user_id=user_id).data()
    return [r['hotel_id'] for r in result]