"""
src/extraccion_subgrafos/subgrafo_interaccion/utils_interaction_patterns.py
Extrae subgrafos del grafo 'expanded-recommendations':
  Usuario_Objetivo → Hotel_Compartido ← Usuario_Intermedio → Hotel_Recomendado
"""
import sys
from pathlib import Path

import os
from pathlib import Path
from py2neo import Graph

# ============================================================
# CONFIGURACIÓN NEO4J
# ============================================================
NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test12345")


def get_expanded_graph():
    return Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), name="expanded-recommendations")


def get_subgraph_for_user_and_hotel(user_id: int, recommended_hotel_id: int):
    """
    Extrae el subgrafo de interacciones para un usuario y un hotel recomendado.
    Patrón: Usuario_Objetivo → Hotel_Compartido ← Usuario_Intermedio → Hotel_Recomendado
    """
    graph = get_expanded_graph()

    query = """
    MATCH (u_obj:User {id: $user_id})
    MATCH (h_rec:Business {id: $hotel_id})
    MATCH path = (u_obj)-[:RATED]->(h_shared:Business)<-[:RATED]-(u_inter:User)-[:RATED]->(h_rec)
    WHERE u_inter.id <> u_obj.id
    RETURN
        u_obj,
        h_rec,
        collect(DISTINCT u_inter) as intermediate_users,
        collect(DISTINCT h_shared) as shared_hotels
    LIMIT 1
    """

    result = graph.run(query, user_id=user_id, hotel_id=recommended_hotel_id).data()

    if not result:
        print(f"  ⚠️  Sin conexión entre usuario {user_id} y hotel {recommended_hotel_id}")
        return None

    record = result[0]
    nodes = []
    relationships = []
    node_id_map = {}

    # Usuario objetivo
    u_obj = record['u_obj']
    u_obj_id = str(u_obj.identity)
    nodes.append({"id": u_obj_id, "labels": ["User"],
                  "properties": {"id": u_obj['id'], "type": "objetivo"}})
    node_id_map[u_obj['id']] = u_obj_id

    # Hotel recomendado
    h_rec = record['h_rec']
    h_rec_id = str(h_rec.identity)
    nodes.append({"id": h_rec_id, "labels": ["Business"],
                  "properties": {"id": h_rec['id'], "type": "recomendado"}})
    node_id_map[h_rec['id']] = h_rec_id

    # Usuarios intermedios
    for u_inter in record.get('intermediate_users', []):
        if u_inter:
            u_inter_id = str(u_inter.identity)
            nodes.append({"id": u_inter_id, "labels": ["User"],
                          "properties": {"id": u_inter['id'], "type": "intermedio"}})
            node_id_map[u_inter['id']] = u_inter_id

    # Hoteles compartidos
    for h_shared in record.get('shared_hotels', []):
        if h_shared:
            h_shared_id = str(h_shared.identity)
            nodes.append({"id": h_shared_id, "labels": ["Business"],
                          "properties": {"id": h_shared['id'], "type": "compartido"}})
            node_id_map[h_shared['id']] = h_shared_id

    # Relaciones
    rel_query = """
    MATCH (u_obj:User {id: $user_id})
    MATCH (h_rec:Business {id: $hotel_id})
    MATCH path = (u_obj)-[r1:RATED]->(h_shared:Business)<-[r2:RATED]-(u_inter:User)-[r3:RATED]->(h_rec)
    WHERE u_inter.id <> u_obj.id
    RETURN r1, r2, r3,
           startNode(r1).id as s1, endNode(r1).id as e1,
           startNode(r2).id as s2, endNode(r2).id as e2,
           startNode(r3).id as s3, endNode(r3).id as e3
    LIMIT 100
    """

    rel_result = graph.run(rel_query, user_id=user_id, hotel_id=recommended_hotel_id).data()

    for i, rel_record in enumerate(rel_result):
        base = i * 3
        relationships.append({
            "id": f"rel_{base}",   "type": "RATED",
            "start_node_id": node_id_map.get(rel_record['s1'], str(rel_record['s1'])),
            "end_node_id":   node_id_map.get(rel_record['e1'], str(rel_record['e1'])),
            "properties": {"rating": float(rel_record['r1']['rating'])}
        })
        relationships.append({
            "id": f"rel_{base+1}", "type": "RATED",
            "start_node_id": node_id_map.get(rel_record['s2'], str(rel_record['s2'])),
            "end_node_id":   node_id_map.get(rel_record['e2'], str(rel_record['e2'])),
            "properties": {"rating": float(rel_record['r2']['rating'])}
        })
        relationships.append({
            "id": f"rel_{base+2}", "type": "RATED",
            "start_node_id": node_id_map.get(rel_record['s3'], str(rel_record['s3'])),
            "end_node_id":   node_id_map.get(rel_record['e3'], str(rel_record['e3'])),
            "properties": {"rating": float(rel_record['r3']['rating'])}
        })

    return nodes, relationships