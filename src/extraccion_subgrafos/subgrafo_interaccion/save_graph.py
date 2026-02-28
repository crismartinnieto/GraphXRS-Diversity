"""
src/extraccion_subgrafos/subgrafo_interaccion/save_graph.py
Guarda subgrafos de interacción en JSON usando la ruta de config.
"""
import json
import sys
from pathlib import Path

# ============================================================
# MODE: 'muestra' o 'completo'
# ============================================================
MODE = "muestra"  # Cambiar a "completo" para procesar todos los usuarios

# ============================================================
# RUTAS RELATIVAS AL DIRECTORIO DE TRABAJO (raíz del proyecto)
# Ejecutar siempre desde: Sistema_recomendacion_xai_TFM_MUSII_CMN/
# ============================================================
PROJECT_ROOT = Path(".")  # Directorio de trabajo = raíz del proyecto

DATA_DIR = PROJECT_ROOT / "data"
SUBGRAFOS_INTERACCIONES = DATA_DIR / f"subgrafos_interacciones_{MODE}"




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