from py2neo import Graph
import os

uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "test12345")

def get_expanded_graph():
    return Graph(uri, auth=(user, password), name="expanded-recommendations")


def get_subgraph_for_user_and_hotel(user_id: int, recommended_hotel_id: int):
    """
    Extrae el subgrafo de interacciones para un usuario y un hotel recomendado.
    
    BUSCA CAMINOS ASÍ:
    Usuario_Objetivo → Hotel_Compartido ← Usuario_Intermedio → Hotel_Recomendado
    
    Es decir: usuarios que valoraron los MISMOS hoteles que tú 
    y que TAMBIÉN valoraron el hotel que se te recomienda
    """
    graph = get_expanded_graph()
    
    # Query para encontrar caminos entre el usuario y el hotel recomendado
    query = """
    MATCH (u_obj:User {id: $user_id})
    MATCH (h_rec:Business {id: $hotel_id})
    
    // Caminos: Usuario -> Hotel compartido <- Usuario intermedio -> Hotel recomendado
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
        print(f"❌ No se encontró conexión entre usuario {user_id} y hotel {recommended_hotel_id}")
        return None
    
    record = result[0]
    
    # Convertir a formato JSON-serializable
    nodes = []
    relationships = []
    node_id_map = {}  # Para mapear identities de Neo4j
    
    # 1. Usuario objetivo
    u_obj = record['u_obj']
    u_obj_id = str(u_obj.identity)
    nodes.append({
        "id": u_obj_id,
        "labels": ["User"],
        "properties": {"id": u_obj['id'], "type": "objetivo"}
    })
    node_id_map[u_obj['id']] = u_obj_id
    
    # 2. Hotel recomendado
    h_rec = record['h_rec']
    h_rec_id = str(h_rec.identity)
    nodes.append({
        "id": h_rec_id,
        "labels": ["Business"],
        "properties": {"id": h_rec['id'], "type": "recomendado"}
    })
    node_id_map[h_rec['id']] = h_rec_id
    
    # 3. Usuarios intermedios
    for u_inter in record.get('intermediate_users', []):
        if u_inter:
            u_inter_id = str(u_inter.identity)
            nodes.append({
                "id": u_inter_id,
                "labels": ["User"],
                "properties": {"id": u_inter['id'], "type": "intermedio"}
            })
            node_id_map[u_inter['id']] = u_inter_id
    
    # 4. Hoteles compartidos
    for h_shared in record.get('shared_hotels', []):
        if h_shared:
            h_shared_id = str(h_shared.identity)
            nodes.append({
                "id": h_shared_id,
                "labels": ["Business"],
                "properties": {"id": h_shared['id'], "type": "compartido"}
            })
            node_id_map[h_shared['id']] = h_shared_id
    
    # 5. Obtener TODAS las relaciones del camino
    rel_query = """
    MATCH (u_obj:User {id: $user_id})
    MATCH (h_rec:Business {id: $hotel_id})
    MATCH path = (u_obj)-[r1:RATED]->(h_shared:Business)<-[r2:RATED]-(u_inter:User)-[r3:RATED]->(h_rec)
    WHERE u_inter.id <> u_obj.id
    RETURN r1, r2, r3, startNode(r1).id as s1, endNode(r1).id as e1,
           startNode(r2).id as s2, endNode(r2).id as e2,
           startNode(r3).id as s3, endNode(r3).id as e3
    LIMIT 100
    """
    
    rel_result = graph.run(rel_query, user_id=user_id, hotel_id=recommended_hotel_id).data()
    
    rel_counter = 0
    for rel_record in rel_result:
        # Relación 1: Usuario objetivo → Hotel compartido
        relationships.append({
            "id": f"rel_{rel_counter}",
            "type": "RATED",
            "start_node_id": node_id_map.get(rel_record['s1'], str(rel_record['s1'])),
            "end_node_id": node_id_map.get(rel_record['e1'], str(rel_record['e1'])),
            "properties": {"rating": float(rel_record['r1']['rating'])}
        })
        rel_counter += 1
        
        # Relación 2: Usuario intermedio → Hotel compartido
        relationships.append({
            "id": f"rel_{rel_counter}",
            "type": "RATED",
            "start_node_id": node_id_map.get(rel_record['s2'], str(rel_record['s2'])),
            "end_node_id": node_id_map.get(rel_record['e2'], str(rel_record['e2'])),
            "properties": {"rating": float(rel_record['r2']['rating'])}
        })
        rel_counter += 1
        
        # Relación 3: Usuario intermedio → Hotel recomendado
        relationships.append({
            "id": f"rel_{rel_counter}",
            "type": "RATED",
            "start_node_id": node_id_map.get(rel_record['s3'], str(rel_record['s3'])),
            "end_node_id": node_id_map.get(rel_record['e3'], str(rel_record['e3'])),
            "properties": {"rating": float(rel_record['r3']['rating'])}
        })
        rel_counter += 1
    
    return nodes, relationships