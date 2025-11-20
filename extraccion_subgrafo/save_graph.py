import json
import os

def save_subgraph_to_json(nodes, relationships, filename):
    """
    Guarda los nodos y relaciones del subgrafo en formato JSON
    dentro de data/subgrafos.
    """
    # Carpeta destino
    output_dir = os.path.join(os.path.dirname(__file__), "data", "subgrafos")
    os.makedirs(output_dir, exist_ok=True)

    save_path = os.path.join(output_dir, filename)

    # Convertir nodos a diccionarios simples
    nodes_data = []
    for node in nodes:
        nodes_data.append({
            "id": node["id"],
            "labels": list(node.labels),
            "properties": dict(node)
        })

    # Convertir relaciones a diccionarios simples
    relationships_data = []
    for rel in relationships:
        relationships_data.append({
            "start_node": rel.start_node["id"],
            "end_node": rel.end_node["id"],
            "type": type(rel).__name__,
            "properties": dict(rel)
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
