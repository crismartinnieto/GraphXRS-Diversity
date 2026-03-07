"""
src/pipeline.py

Pipeline atómico unificado para el sistema XAI de recomendación.

Flujo completo por cada par (usuario, hotel_recomendado):

  KG (Conocimiento):
    1. Consulta histórico del usuario en 'interactions'
    2. Extrae subgrafo de 'knowledge' (hotel_rec + hoteles históricos)
    3. Calcula métricas KG en memoria
    4. JSON temporal se borra automáticamente al terminar

  CF (Interacción):
    1. Añade enlace temporal en 'interactions' (sin rating)
    2. Extrae subgrafo CF con patrón usuario→compartido←intermedio→recomendado
    3. Elimina enlace temporal (siempre, incluso si hay error)
    4. Calcula métricas CF en memoria
    5. JSON temporal se borra automáticamente al terminar

OUTPUT (un CSV por métrica por usuario, igual que antes):
    output/
      metricas_grafo_conocimiento_muestra/
        kg_usuario_3_kg_num_propiedades_compartidas_TIMESTAMP.csv
        kg_usuario_3_kg_ratio_propiedades_compartidas_TIMESTAMP.csv
        kg_usuario_3_kg_peso_ponderado_perfil_TIMESTAMP.csv
        kg_usuario_3_kg_jaccard_similarity_TIMESTAMP.csv
        ...
      metricas_grafo_interaccion_muestra/
        cf_usuario_3_cf_degree_hotel_TIMESTAMP.csv
        cf_usuario_3_cf_ratio_usuarios_compartidos_TIMESTAMP.csv
        cf_usuario_3_cf_norm_degree_hotel_TIMESTAMP.csv
        ...

    Cada CSV tiene columnas:
        usuario | hotel_recomendado | hotel_explicador | valor_metrica

EJECUTAR DESDE LA RAÍZ DEL PROYECTO:
    python src/pipeline.py --modo muestra
    python src/pipeline.py --modo completo
    python src/pipeline.py --modo muestra --usuarios 3 35 276
"""
import sys
import json
import logging
import argparse
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import pandas as pd

# ============================================================
# RUTAS
# ============================================================
PROJECT_ROOT = Path(".")
DATA_DIR     = PROJECT_ROOT / "data"
RAW_DIR      = DATA_DIR / "raw"
OUTPUT_DIR   = PROJECT_ROOT / "output"
LOGS_DIR     = PROJECT_ROOT / "logs"

CSV_RECOMENDACIONES = RAW_DIR / "relacion_usuario_rating_recomendador.csv"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# AÑADIR src/ AL PATH
# ============================================================
SRC_DIR = Path(__file__).parent
sys.path.insert(0, str(SRC_DIR))

from extraccion_subgrafos.subgrafo_conocimiento.utils_interactions        import get_user_interacted_hotels
from extraccion_subgrafos.subgrafo_conocimiento.utils_knowledge            import get_subgraph_for_hotels
from extraccion_subgrafos.subgrafo_interaccion.utils_interaction_patterns  import get_subgraph_for_user_and_hotel

# Nota: los ficheros se llaman 'métricas.py' (con tilde) — importamos via importlib
import importlib
_mod_kg = importlib.import_module("extraccion_metricas_conocimiento.métricas")
_mod_cf = importlib.import_module("extraccion_metricas_interaccion.métricas")

calcular_metricas_kg  = _mod_kg.calcular_metricas_kg
NOMBRES_METRICAS_KG   = _mod_kg.NOMBRES_METRICAS_KG
calcular_metricas_cf  = _mod_cf.calcular_metricas_cf
NOMBRES_METRICAS_CF   = _mod_cf.NOMBRES_METRICAS_CF


# ============================================================
# LOGGING
# ============================================================
def setup_logging(modo: str) -> logging.Logger:
    log_file = LOGS_DIR / f"pipeline_{modo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger("pipeline")


# ============================================================
# GUARDAR CSVs — UN FICHERO POR MÉTRICA POR USUARIO
# ============================================================

def guardar_csvs_usuario(
    filas: List[Dict],
    usuario: int,
    nombres_metricas: List[str],
    prefijo: str,
    output_dir: Path,
    timestamp: str,
    logger: logging.Logger
):
    """
    Para un usuario, genera un CSV por cada métrica.

    Nombre:   {prefijo}_usuario_{usuario}_{metrica}_{timestamp}.csv
    Columnas: usuario | hotel_recomendado | hotel_explicador | valor_metrica
    """
    if not filas:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(filas)

    for metrica in nombres_metricas:
        if metrica not in df.columns:
            logger.warning(f"  ⚠️  '{metrica}' no encontrada, se omite")
            continue

        df_metrica = (
            df[['usuario', 'hotel_recomendado', 'hotel_explicador', metrica]]
            .copy()
            .rename(columns={metrica: 'valor_metrica'})
        )

        nombre_fichero = f"{prefijo}_usuario_{usuario}_{metrica}_{timestamp}.csv"
        df_metrica.to_csv(output_dir / nombre_fichero, index=False, encoding='utf-8')
        logger.info(f"  💾 {nombre_fichero}  ({len(df_metrica)} filas)")


# ============================================================
# FLUJO ATÓMICO KG
# ============================================================

def procesar_par_kg(user_id: int, hotel_rec: int, logger: logging.Logger) -> List[Dict]:
    """
    Flujo atómico KG para un par (usuario, hotel_rec).
    Devuelve lista de dicts con métricas KG, una fila por hotel_explicador.
    El JSON temporal se crea y borra dentro de esta función.
    """
    try:
        hoteles_historicos = get_user_interacted_hotels(user_id)
        if not hoteles_historicos:
            logger.warning(f"  [KG] Sin histórico para user={user_id}")
            return []

        hotel_ids         = list(set([hotel_rec] + hoteles_historicos))
        nodes_kg, rels_kg = get_subgraph_for_hotels(hotel_ids)

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as tmp:
            json.dump({"nodes": nodes_kg, "relationships": rels_kg}, tmp, ensure_ascii=False)
            tmp_path = Path(tmp.name)

        try:
            filas = calcular_metricas_kg(tmp_path, user_id, hotel_rec, hoteles_historicos)
            for f in filas:
                f['usuario']           = user_id
                f['hotel_recomendado'] = hotel_rec
            logger.info(f"  [KG] {len(filas)} hoteles explicadores")
            return filas
        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"  [KG] Error: {e}")
        return []


# ============================================================
# FLUJO ATÓMICO CF
# ============================================================

def procesar_par_cf(user_id: int, hotel_rec: int, logger: logging.Logger) -> List[Dict]:
    """
    Flujo atómico CF para un par (usuario, hotel_rec).
    El enlace temporal se gestiona dentro de get_subgraph_for_user_and_hotel
    con try/finally → siempre se borra aunque haya error.
    El JSON temporal se crea y borra dentro de esta función.
    """
    try:
        result_cf = get_subgraph_for_user_and_hotel(user_id, hotel_rec)

        if result_cf is None:
            logger.warning(f"  [CF] Sin patrón para user={user_id}, hotel={hotel_rec}")
            return []

        nodes_cf, rels_cf = result_cf

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as tmp:
            json.dump({"nodes": nodes_cf, "relationships": rels_cf}, tmp, ensure_ascii=False)
            tmp_path = Path(tmp.name)

        try:
            filas = calcular_metricas_cf(tmp_path, user_id, hotel_rec)
            for f in filas:
                f['usuario']           = user_id
                f['hotel_recomendado'] = hotel_rec
            logger.info(f"  [CF] {len(filas)} hoteles explicadores")
            return filas
        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"  [CF] Error: {e}")
        return []


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Pipeline XAI atómico KG + CF")
    parser.add_argument(
        "--modo", choices=["muestra", "completo"], default="muestra",
        help="'muestra' filtra por --usuarios, 'completo' procesa todos"
    )
    parser.add_argument(
        "--usuarios", nargs="+", type=int, default=[3, 35],
        help="IDs de usuarios para modo muestra (default: 3 35)"
    )
    args = parser.parse_args()

    logger    = setup_logging(args.modo)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    dir_kg = OUTPUT_DIR / f"metricas_grafo_conocimiento_{args.modo}"
    dir_cf = OUTPUT_DIR / f"metricas_grafo_interaccion_{args.modo}"

    logger.info("=" * 70)
    logger.info(f"PIPELINE XAI — MODO={args.modo.upper()}")
    logger.info(f"Timestamp : {timestamp}")
    logger.info(f"Métricas KG ({len(NOMBRES_METRICAS_KG)}): {NOMBRES_METRICAS_KG}")
    logger.info(f"Métricas CF ({len(NOMBRES_METRICAS_CF)}): {NOMBRES_METRICAS_CF}")
    logger.info("=" * 70)

    if not CSV_RECOMENDACIONES.exists():
        logger.error(f"❌ No existe: {CSV_RECOMENDACIONES}")
        sys.exit(1)

    df = pd.read_csv(CSV_RECOMENDACIONES)
    logger.info(f"📂 Recomendaciones: {len(df)} filas")

    if args.modo == "muestra":
        df = df[df['usuario'].isin(args.usuarios)]
        logger.info(f"🔍 Usuarios: {args.usuarios} → {len(df)} pares")

    # Acumulador por usuario hasta tener todos sus pares procesados
    # {user_id: {'kg': [filas...], 'cf': [filas...]}}
    acumulador: Dict[int, Dict] = defaultdict(lambda: {'kg': [], 'cf': []})
    errores = 0
    total   = len(df)

    for idx, row in df.iterrows():
        user_id   = int(row['usuario'])
        hotel_rec = int(row['negocio'])

        logger.info(f"\n{'─'*50}")
        logger.info(f"Par {idx+1}/{total}: user={user_id}, hotel_rec={hotel_rec}")
        t0 = time.time()

        try:
            filas_kg = procesar_par_kg(user_id, hotel_rec, logger)
            filas_cf = procesar_par_cf(user_id, hotel_rec, logger)

            acumulador[user_id]['kg'].extend(filas_kg)
            acumulador[user_id]['cf'].extend(filas_cf)

            logger.info(
                f"  ✅ OK ({time.time()-t0:.2f}s) "
                f"KG:{len(filas_kg)} CF:{len(filas_cf)} filas"
            )
        except Exception as e:
            logger.error(f"  ❌ Error inesperado: {e}")
            errores += 1

    # ── Guardar CSVs una vez procesados TODOS los pares del usuario ──
    logger.info(f"\n{'='*70}")
    logger.info("GUARDANDO CSVs POR MÉTRICA POR USUARIO...")
    logger.info(f"{'='*70}")

    for usuario, datos in acumulador.items():
        logger.info(f"\n👤 Usuario {usuario}:")
        guardar_csvs_usuario(datos['kg'], usuario, NOMBRES_METRICAS_KG, 'kg', dir_kg, timestamp, logger)
        guardar_csvs_usuario(datos['cf'], usuario, NOMBRES_METRICAS_CF, 'cf', dir_cf, timestamp, logger)

    n_kg = len(list(dir_kg.glob("*.csv"))) if dir_kg.exists() else 0
    n_cf = len(list(dir_cf.glob("*.csv"))) if dir_cf.exists() else 0

    logger.info(f"\n{'='*70}")
    logger.info("✅ PIPELINE COMPLETADO")
    logger.info(f"   Usuarios  : {len(acumulador)}")
    logger.info(f"   Errores   : {errores}")
    logger.info(f"   CSVs KG   : {n_kg}  →  {dir_kg}")
    logger.info(f"   CSVs CF   : {n_cf}  →  {dir_cf}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()