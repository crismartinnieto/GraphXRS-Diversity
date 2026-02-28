"""
src/extraccion_subgrafos/save_graph.py
Guarda subgrafos en formato JSON en las carpetas correctas según config.
"""
import json
import sys
from pathlib import Path

# ============================================================
# MODE: 'muestra' o 'completo'
# ============================================================
MODE = "muestra"  # Cambiar a "completo" para procesar todos los usuarios

# ============================================================
# DEFINICIÓN DE RUTAS RELATIVAS (desde la ubicación de este script)
# ============================================================
# Este script está en: src/extraccion_subgrafos/subgrafo_conocimiento/save_graph.py
SCRIPT_DIR = Path(__file__).parent  # .../subgrafo_conocimiento/

# Subir niveles hasta llegar a la raíz
# ../  → extraccion_subgrafos/
# ../../  → src/
# ../../../  → raíz del proyecto
PROJECT_ROOT = SCRIPT_DIR / ".." / ".." / ".."

# Definir rutas relativas desde la raíz
DATA_DIR = PROJECT_ROOT / "data"
SUBGRAFOS_CONOCIMIENTO = DATA_DIR / f"subgrafos_conocimiento_{MODE}"


def save_subgraph_to_json(nodes, relationships, filename):
    """
    Guarda nodos y relaciones en JSON dentro de la carpeta
    subgrafos_conocimiento_muestra o subgrafos_conocimiento_completo
    según el MODE definido en config.py
    """
    output_dir = SUBGRAFOS_CONOCIMIENTO
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / filename

    subgraph_data = {
        "nodes": [
            {"id": n["id"], "labels": n["labels"], "properties": n["properties"]}
            for n in nodes
        ],
        "relationships": [
            {
                "id":         r["id"],
                "start_node": r["start_node_id"],
                "end_node":   r["end_node_id"],
                "type":       r["type"],
                "properties": r["properties"]
            }
            for r in relationships
        ]
    }

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(subgraph_data, f, ensure_ascii=False, indent=4)

    print(f"✅ Subgrafo guardado en: {save_path}")
    return save_path