"""
src/extraccion_subgrafos/subgrafo_interaccion/extract_interaction_subgraphs.py
Script principal para extraer subgrafos de interacción por usuario.
Ejecuta en modo 'muestra' o 'completo' según config.py.
"""
import sys
import time
import logging
from pathlib import Path

import sys
from pathlib import Path

# ============================================================
# AÑADIR RAÍZ DEL PROYECTO AL PYTHONPATH
# ============================================================
current_file = Path(__file__).resolve()

for parent in current_file.parents:
    if (parent / "config.py").exists():
        sys.path.insert(0, str(parent))
        break

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CSV_USUARIO_RATING_RECOMEND, LOGS_DIR, MODE, USUARIOS_MUESTRA

import pandas as pd
from utils_interaction_patterns import get_subgraph_for_user_and_hotel
from save_graph import save_subgraph_to_json

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "extraccion_subgrafos_interaccion.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def extract_user_interaction_subgraph(user_id: int, recommended_hotel: int):
    """Extrae y guarda el subgrafo de interacciones para un usuario + hotel."""
    start = time.time()
    logger.info(f"▶️  user={user_id}, hotel_recomendado={recommended_hotel}")

    result = get_subgraph_for_user_and_hotel(user_id, recommended_hotel)

    if result is None:
        logger.warning(f"  ⚠️  Sin resultado para user={user_id}, hotel={recommended_hotel}")
        return None

    nodes, relationships = result
    logger.info(f"  Nodos: {len(nodes)} | Relaciones: {len(relationships)}")

    filename = f"user_{user_id}_hotel_{recommended_hotel}_interactions.json"
    save_path = save_subgraph_to_json(nodes, relationships, filename)

    logger.info(f"  ✅ Guardado en {save_path} ({time.time()-start:.2f}s)")
    return save_path


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info(f"EXTRACCIÓN SUBGRAFOS INTERACCIÓN — MODE={MODE}")
    logger.info("=" * 70)

    if not CSV_USUARIO_RATING_RECOMEND.exists():
        logger.error(f"❌ No se encuentra: {CSV_USUARIO_RATING_RECOMEND}")
        sys.exit(1)

    df = pd.read_csv(CSV_USUARIO_RATING_RECOMEND)
    logger.info(f"📂 CSV cargado: {len(df)} filas")

    if MODE == "muestra":
        df = df[df['usuario'].isin(USUARIOS_MUESTRA)]
        logger.info(f"🔍 Modo MUESTRA: {len(df)} filas para usuarios {USUARIOS_MUESTRA}")
    else:
        logger.info(f"🔍 Modo COMPLETO: {len(df)} filas")

    procesados = 0
    fallidos   = 0

    for idx, row in df.iterrows():
        result = extract_user_interaction_subgraph(int(row['usuario']), int(row['negocio']))
        if result:
            procesados += 1
        else:
            fallidos += 1

    logger.info("=" * 70)
    logger.info(f"COMPLETADO — Exitosos: {procesados} | Fallidos: {fallidos}")
    logger.info("=" * 70)