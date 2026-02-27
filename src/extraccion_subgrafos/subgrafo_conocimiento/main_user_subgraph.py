"""
src/extraccion_subgrafos/main_user_subgraph.py
Script principal para extraer subgrafos de conocimiento por usuario.
Ejecuta en modo 'muestra' (5 usuarios) o 'completo' según config.py
"""
import sys
import time
import logging
from pathlib import Path

from pathlib import Path
import sys

# Obtener raíz del proyecto (nueva_estructura)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Añadirla al sys.path
sys.path.insert(0, str(PROJECT_ROOT))

# Añadir src/ al path para importar config y utils del mismo módulo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    CSV_USUARIO_RATING_RECOMEND,
    LOGS_DIR,
    MODE,
    USUARIOS_MUESTRA
)

import pandas as pd
from utils_interactions import get_user_interacted_hotels
from utils_knowledge import get_subgraph_for_hotels
from save_graph import save_subgraph_to_json

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "extraccion_subgrafos.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def extract_user_subgraph(user_id: int, recommended_hotel: int):
    """
    Proceso completo para un usuario + hotel recomendado:
      1. Obtiene hoteles con los que ya interactuó el usuario.
      2. Forma el conjunto: [hotel_recomendado + interacciones previas]
      3. Extrae el subgrafo del grafo de conocimiento.
      4. Lo guarda como JSON en la carpeta configurada.
    """
    start = time.time()
    logger.info(f"▶️  Procesando user={user_id}, hotel_recomendado={recommended_hotel}")

    user_hotels = get_user_interacted_hotels(user_id)
    logger.info(f"   Hoteles previos: {user_hotels}")

    hotel_ids = list(set([recommended_hotel] + user_hotels))
    logger.info(f"   Hoteles en subgrafo: {hotel_ids}")

    nodes, relationships = get_subgraph_for_hotels(hotel_ids)
    logger.info(f"   Nodos: {len(nodes)}, Relaciones: {len(relationships)}")

    filename = f"user_{user_id}_hotel_{recommended_hotel}.json"
    save_path = save_subgraph_to_json(nodes, relationships, filename)

    elapsed = time.time() - start
    logger.info(f"✅ Guardado en {save_path} ({elapsed:.2f}s)\n")
    return save_path


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info(f"EXTRACCIÓN DE SUBGRAFOS — MODE={MODE}")
    logger.info("=" * 70)

    # Cargar CSV de recomendaciones
    if not CSV_USUARIO_RATING_RECOMEND.exists():
        logger.error(f"❌ No se encuentra: {CSV_USUARIO_RATING_RECOMEND}")
        sys.exit(1)

    df = pd.read_csv(CSV_USUARIO_RATING_RECOMEND)
    logger.info(f"📂 CSV cargado: {len(df)} filas")

    # Filtrar según modo
    if MODE == "muestra":
        df = df[df['usuario'].isin(USUARIOS_MUESTRA)]
        logger.info(f"🔍 Modo MUESTRA: {len(df)} filas para usuarios {USUARIOS_MUESTRA}")
    else:
        logger.info(f"🔍 Modo COMPLETO: {len(df)} filas")

    # Extraer subgrafo por cada combinación usuario–hotel
    errores = 0
    for idx, row in df.iterrows():
        try:
            extract_user_subgraph(int(row['usuario']), int(row['negocio']))
        except Exception as e:
            logger.error(f"❌ Error en fila {idx} (user={row['usuario']}, hotel={row['negocio']}): {e}")
            errores += 1

    logger.info("=" * 70)
    logger.info(f"PROCESO COMPLETADO — Errores: {errores}")
    logger.info("=" * 70)