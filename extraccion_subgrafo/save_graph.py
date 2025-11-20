import json
import os

def save_subgraph_to_json(nodes, relationships, filename):
    """
    Guarda los nodos y relaciones del subgrafo en formato JSON
    dentro de data/subgrafos.
    
    nodes: lista de dicts con 'id', 'labels', 'properties'
    relationships: lista de dicts con 'id', 'type', 'start_node_id', 'end_node_id', 'properties'
    """
    # Carpeta destino
    output_dir = os.path.join(os.path.dirname(__file__), "data", "subgrafos")
    os.makedirs(output_dir, exist_ok=True)

    save_path = os.path.join(output_dir, filename)

    # Convertir nodos a diccionarios simples (ya vienen así)
    nodes_data = []
    for node in nodes:
        nodes_data.append({
            "id": node["id"],
            "labels": node["labels"],
            "properties": node["properties"]
        })

    # Convertir relaciones a diccionarios simples (ya vienen así)
    relationships_data = []
    for rel in relationships:
        relationships_data.append({
            "id": rel["id"],
            "start_node": rel["start_node_id"],
            "end_node": rel["end_node_id"],
            "type": rel["type"],
            "properties": rel["properties"]
        })

    # Estructura final
    subgraph_data = {
        "nodes": nodes_data,
        "relationships": relationships_data
    }

    # Guardar en JSON
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(subgraph_data, f, ensure_ascii=False, indent=4)

    print(f"Subgrafo guardado en JSON en: {save_path}")
    return save_path
