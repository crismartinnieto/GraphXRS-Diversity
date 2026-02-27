"""
src/extraccion_subgrafos/subgrafo_interaccion/save_graph.py
Guarda subgrafos de interacción en JSON usando la ruta de config.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import SUBGRAFOS_INTERACCIONES


def save_subgraph_to_json(nodes, relationships, filename):
    """Guarda nodos y relaciones en JSON dentro de subgrafos_interacciones_muestra/completo."""
    output_dir = SUBGRAFOS_INTERACCIONES
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / filename

    subgraph_data = {
        "nodes": nodes,
        "relationships": relationships
    }

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(subgraph_data, f, ensure_ascii=False, indent=4)

    print(f"  ✅ Guardado: {save_path}")
    return save_path