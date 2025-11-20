from py2neo import Graph
import os

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "test12345")

def get_interactions_graph():
    # Apuntar explícitamente a la base 'interactions'
    return Graph(uri, auth=(user, password), name="interactions")


def get_user_interacted_hotels(user_id: int):
    """
    Devuelve la lista de hoteles con los que el usuario ha interactuado.
    """
    graph = get_interactions_graph()  # <- debe apuntar a 'interactions'
    query = """
    MATCH (u:User {id: $user_id})-[:RATED]->(b:Business)
    RETURN b.id AS hotel_id
    """
    result = graph.run(query, user_id=user_id).data()
    return [r['hotel_id'] for r in result]
