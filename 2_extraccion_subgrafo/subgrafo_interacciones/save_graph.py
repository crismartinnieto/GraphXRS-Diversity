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

    # Estructura final
    subgraph_data = {
        "nodes": nodes,
        "relationships": relationships
    }

    # Guardar en JSON
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(subgraph_data, f, ensure_ascii=False, indent=4)

    print(f"✅ Subgrafo guardado: {save_path}")
    return save_path