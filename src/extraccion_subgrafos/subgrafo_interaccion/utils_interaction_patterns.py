"""
src/extraccion_subgrafos/subgrafo_interaccion/utils_interaction_patterns.py

Extrae subgrafos del grafo 'interactions' (datos reales) usando enlace temporal.

Patrón CF:
  Usuario_Objetivo → Hotel_Compartido ← Usuario_Intermedio → Hotel_Recomendado

El hotel recomendado se añade temporalmente a 'interactions' SIN rating,
se extrae el subgrafo, y se elimina el enlace al terminar.
Así 'interactions' siempre queda limpio.
"""
import os
from py2neo import Graph

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test12345")


def get_interactions_graph():
    return Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), name="interactions")


def _add_temp_link(graph, user_id: int, hotel_id: int):
    """Añade enlace temporal (sin rating) entre usuario y hotel recomendado."""
    graph.run("""
        MERGE (u:User {id: $user_id})
        MERGE (b:Business {id: $hotel_id})
        MERGE (u)-[:RATED]->(b)
    """, user_id=user_id, hotel_id=hotel_id)


def _remove_temp_link(graph, user_id: int, hotel_id: int):
    """
    Elimina el enlace temporal SOLO si no tenía rating previo (es decir, era sintético).
    Así no borramos interacciones reales si el hotel ya estaba en el histórico.
    """
    graph.run("""
        MATCH (u:User {id: $user_id})-[r:RATED]->(b:Business {id: $hotel_id})
        WHERE r.rating IS NULL
        DELETE r
    """, user_id=user_id, hotel_id=hotel_id)


def get_subgraph_for_user_and_hotel(user_id: int, recommended_hotel_id: int):
    """
    Flujo atómico:
      1. Añade enlace temporal (u)-[:RATED]->(h_rec) sin rating
      2. Extrae subgrafo CF con el patrón completo
      3. Elimina el enlace temporal
      4. Devuelve (nodes, relationships) o None si no hay patrón
    """
    graph = get_interactions_graph()

    # 1. Enlace temporal
    _add_temp_link(graph, user_id, recommended_hotel_id)

    try:
        # 2. Extraer nodos del patrón
        query_nodes = """
        MATCH (u_obj:User {id: $user_id})
        MATCH (h_rec:Business {id: $hotel_id})
        MATCH (u_obj)-[:RATED]->(h_shared:Business)<-[:RATED]-(u_inter:User)-[:RATED]->(h_rec)
        WHERE u_inter.id <> u_obj.id
        RETURN
            u_obj,
            h_rec,
            collect(DISTINCT u_inter) AS intermediate_users,
            collect(DISTINCT h_shared) AS shared_hotels
        LIMIT 1
        """
        result = graph.run(query_nodes, user_id=user_id, hotel_id=recommended_hotel_id).data()

        if not result:
            print(f"  ⚠️  Sin patrón CF para user={user_id}, hotel={recommended_hotel_id}")
            return None

        record      = result[0]
        nodes       = []
        node_id_map = {}

        # Usuario objetivo
        u_obj    = record['u_obj']
        u_obj_id = str(u_obj.identity)
        nodes.append({"id": u_obj_id, "labels": ["User"],
                      "properties": {"id": u_obj['id'], "type": "objetivo"}})
        node_id_map[u_obj['id']] = u_obj_id

        # Hotel recomendado
        h_rec    = record['h_rec']
        h_rec_id = str(h_rec.identity)
        nodes.append({"id": h_rec_id, "labels": ["Business"],
                      "properties": {"id": h_rec['id'], "type": "recomendado"}})
        node_id_map[h_rec['id']] = h_rec_id

        # Usuarios intermedios
        for u_inter in record.get('intermediate_users', []):
            if u_inter:
                uid = str(u_inter.identity)
                nodes.append({"id": uid, "labels": ["User"],
                              "properties": {"id": u_inter['id'], "type": "intermedio"}})
                node_id_map[u_inter['id']] = uid

        # Hoteles compartidos
        for h_shared in record.get('shared_hotels', []):
            if h_shared:
                hid = str(h_shared.identity)
                nodes.append({"id": hid, "labels": ["Business"],
                              "properties": {"id": h_shared['id'], "type": "compartido"}})
                node_id_map[h_shared['id']] = hid

        # 3. Extraer relaciones — solo interacciones reales (rating IS NOT NULL)
        # El enlace temporal (sin rating) queda excluido automáticamente
        query_rels = """
        MATCH (u_obj:User {id: $user_id})
        MATCH (h_rec:Business {id: $hotel_id})
        MATCH (u_obj)-[r1:RATED]->(h_shared:Business)<-[r2:RATED]-(u_inter:User)-[r3:RATED]->(h_rec)
        WHERE u_inter.id <> u_obj.id
          AND r1.rating IS NOT NULL
          AND r2.rating IS NOT NULL
          AND r3.rating IS NOT NULL
        RETURN r1, r2, r3,
               startNode(r1).id AS s1, endNode(r1).id AS e1,
               startNode(r2).id AS s2, endNode(r2).id AS e2,
               startNode(r3).id AS s3, endNode(r3).id AS e3
        LIMIT 100
        """
        rel_result    = graph.run(query_rels, user_id=user_id, hotel_id=recommended_hotel_id).data()
        relationships = []

        for i, rec in enumerate(rel_result):
            base = i * 3
            relationships.append({
                "id": f"rel_{base}", "type": "RATED",
                "start_node_id": node_id_map.get(rec['s1'], str(rec['s1'])),
                "end_node_id":   node_id_map.get(rec['e1'], str(rec['e1'])),
                "properties":    {"rating": float(rec['r1']['rating'])}
            })
            relationships.append({
                "id": f"rel_{base+1}", "type": "RATED",
                "start_node_id": node_id_map.get(rec['s2'], str(rec['s2'])),
                "end_node_id":   node_id_map.get(rec['e2'], str(rec['e2'])),
                "properties":    {"rating": float(rec['r2']['rating'])}
            })
            relationships.append({
                "id": f"rel_{base+2}", "type": "RATED",
                "start_node_id": node_id_map.get(rec['s3'], str(rec['s3'])),
                "end_node_id":   node_id_map.get(rec['e3'], str(rec['e3'])),
                "properties":    {"rating": float(rec['r3']['rating'])}
            })

        return nodes, relationships

    finally:
        # 4. SIEMPRE eliminar el enlace temporal, aunque haya error
        _remove_temp_link(graph, user_id, recommended_hotel_id)