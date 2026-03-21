"""
src/pipeline.py

EJECUTAR:
    python src/pipeline.py --modo muestra
    python src/pipeline.py --modo muestra --usuarios 3 35
    python src/pipeline.py --modo muestra --usuarios 3 --debug --hotel 45
    python src/pipeline.py --modo completo

MODO DEBUG:
    Añade --debug para guardar los JSONs de subgrafos y un informe de validación.
    Añade --hotel X para limitar el debug a un único par (usuario, hotel).

    Genera en output/debug/:
        kg_user{U}_hotel{H}_subgrafo.json     ← nodos y relaciones del KG
        cf_user{U}_hotel{H}_subgrafo.json     ← nodos y relaciones del CF
        validacion_user{U}_hotel{H}.txt       ← cálculo paso a paso legible
"""
from asyncio.log import logger
import sys
import json
import logging
import argparse
import tempfile
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd

# ============================================================
# RUTAS
# ============================================================
PROJECT_ROOT = Path(".")
DATA_DIR     = PROJECT_ROOT / "data"
RAW_DIR      = DATA_DIR / "raw"
OUTPUT_DIR   = PROJECT_ROOT / "output"
LOGS_DIR     = PROJECT_ROOT / "logs"
DEBUG_DIR    = OUTPUT_DIR / "debug"

CSV_RECOMENDACIONES = DATA_DIR / "recomendaciones_del_modelo" / "relacion_usuario_rating_recomendador.csv"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_DIR.mkdir(parents=True, exist_ok=True)
# ============================================================
# AÑADIR src/ AL PATH
# ============================================================
SRC_DIR = Path(__file__).parent
sys.path.insert(0, str(SRC_DIR))

from extraccion_subgrafos.subgrafo_conocimiento.utils_interactions        import get_user_interacted_hotels
from extraccion_subgrafos.subgrafo_conocimiento.utils_knowledge            import get_subgraph_for_hotels
from extraccion_subgrafos.subgrafo_interaccion.utils_interaction_patterns  import get_subgraph_for_user_and_hotel

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
# DEBUG — guardar JSON + informe de validación legible
# ============================================================

def _propiedades_de_hotel(nodes: list, relationships: list, hotel_node_id: str):
    """Extrae propiedades de un hotel dado su node_id interno."""
    node_by_id = {n['id']: n for n in nodes}
    props = set()
    for rel in relationships:
        start = rel.get('start_node') or rel.get('start_node_id')
        end   = rel.get('end_node')   or rel.get('end_node_id')
        if start == hotel_node_id:
            dest = node_by_id.get(end)
            if dest and 'name' in dest.get('properties', {}):
                props.add(dest['properties']['name'])
    return props


def guardar_debug_kg(
    user_id: int, hotel_rec: int,
    nodes: list, rels: list,
    hoteles_historicos: list,
    metricas_resultado: list
):
    """Guarda JSON del subgrafo KG + informe de validación paso a paso."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. JSON crudo del subgrafo
    json_path = DEBUG_DIR / f"kg_user{user_id}_hotel{hotel_rec}_subgrafo.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"nodes": nodes, "relationships": rels}, f, ensure_ascii=False, indent=2)

    # 2. Informe legible
    txt_path = DEBUG_DIR / f"validacion_kg_user{user_id}_hotel{hotel_rec}.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:

        f.write(f"{'='*60}\n")
        f.write(f"VALIDACIÓN KG — usuario={user_id}, hotel_recomendado={hotel_rec}\n")
        f.write(f"{'='*60}\n\n")

        # Mapear hotel_id real → node_id interno
        hotel_node_map = {}
        for node in nodes:
            if 'Business' in node.get('labels', []):
                real_id = str(node['properties'].get('id', ''))
                hotel_node_map[real_id] = node['id']

        # Propiedades del hotel recomendado
        node_id_rec = hotel_node_map.get(str(hotel_rec), '')
        props_rec = _propiedades_de_hotel(nodes, rels, node_id_rec)
        f.write(f"HOTEL RECOMENDADO ({hotel_rec}) — {len(props_rec)} propiedades:\n")
        for p in sorted(props_rec):
            f.write(f"    {p}\n")
        f.write("\n")

        # Propiedades de cada hotel histórico + intersección manual
        hist_strs = [str(h) for h in hoteles_historicos]
        for hist_id_str in hist_strs:
            node_id_hist = hotel_node_map.get(hist_id_str, '')
            props_hist   = _propiedades_de_hotel(nodes, rels, node_id_hist)
            interseccion = props_rec & props_hist
            union        = props_rec | props_hist

            f.write(f"HOTEL HISTÓRICO ({hist_id_str}) — {len(props_hist)} propiedades:\n")
            for p in sorted(props_hist):
                marker = " ✓" if p in interseccion else ""
                f.write(f"    {p}{marker}\n")

            ratio = len(interseccion)/len(props_hist) if props_hist else 0.0
            jaccard = len(interseccion)/len(union) if union else 0.0
            
            f.write(f"\n  → Propiedades compartidas ({len(interseccion)}): {sorted(interseccion)}\n")
            f.write(f"  → kg_num_propiedades_compartidas : {float(len(interseccion))}\n")
            f.write(f"  → kg_ratio_propiedades_compartidas: {ratio:.4f}  ({len(interseccion)}/{len(props_hist)})\n")
            f.write(f"  → kg_jaccard_similarity          : {jaccard:.4f}  ({len(interseccion)}/{len(union)})\n")
            f.write("\n")

        # Resultado real del código
        f.write(f"{'─'*60}\n")
        f.write("RESULTADO REAL DEL CÓDIGO:\n")
        for fila in metricas_resultado:
            f.write(f"\n  hotel_explicador={fila.get('hotel_explicador')}\n")
            for k, v in fila.items():
                if k not in ('usuario', 'hotel_recomendado', 'hotel_explicador'):
                    f.write(f"    {k}: {v}\n")

    return json_path, txt_path


def guardar_debug_cf(
    user_id: int, hotel_rec: int,
    nodes: list, rels: list,
    metricas_resultado: list
):
    """Guarda JSON del subgrafo CF + informe de validación paso a paso."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. JSON crudo
    json_path = DEBUG_DIR / f"cf_user{user_id}_hotel{hotel_rec}_subgrafo.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({"nodes": nodes, "relationships": rels}, f, ensure_ascii=False, indent=2)

    # 2. Informe legible
    txt_path = DEBUG_DIR / f"validacion_cf_user{user_id}_hotel{hotel_rec}.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:

        f.write(f"{'='*60}\n")
        f.write(f"VALIDACIÓN CF — usuario={user_id}, hotel_recomendado={hotel_rec}\n")
        f.write(f"{'='*60}\n\n")

        # Clasificar nodos
        usuarios_interm  = []
        hoteles_comp     = []
        usuario_obj      = None
        hotel_rec_node   = None

        for node in nodes:
            tipo = node['properties'].get('type', '')
            nid  = node['properties'].get('id', node['id'])
            if 'User' in node.get('labels', []):
                if tipo == 'objetivo':
                    usuario_obj = nid
                elif tipo == 'intermedio':
                    usuarios_interm.append(nid)
            elif 'Business' in node.get('labels', []):
                if tipo == 'recomendado':
                    hotel_rec_node = nid
                elif tipo == 'compartido':
                    hoteles_comp.append(nid)

        f.write(f"Usuario objetivo   : {usuario_obj}\n")
        f.write(f"Hotel recomendado  : {hotel_rec_node}\n")
        f.write(f"Usuarios intermedios ({len(usuarios_interm)}): {sorted(usuarios_interm)}\n")
        f.write(f"Hoteles compartidos ({len(hoteles_comp)}): {sorted(hoteles_comp)}\n\n")

        # Relaciones
        f.write(f"RELACIONES ({len(rels)}):\n")
        for r in rels:
            f.write(f"  {r.get('start_node_id')} -[RATED rating={r.get('properties',{}).get('rating')}]-> {r.get('end_node_id')}\n")

        # Métricas manuales por hotel compartido
        # Construir degree count
        degree = defaultdict(int)
        rels_por_fin = defaultdict(set)
        for r in rels:
            s = r.get('start_node_id')
            e = r.get('end_node_id')
            degree[s] += 1
            degree[e] += 1
            rels_por_fin[e].add(s)

        # Mapear node_id interno → real id
        node_real = {n['id']: n['properties'].get('id', n['id']) for n in nodes}
        usuarios_interm_node_ids = {
            n['id'] for n in nodes
            if 'User' in n.get('labels', []) and n['properties'].get('type') == 'intermedio'
        }

        f.write(f"\n{'─'*60}\n")
        f.write("MÉTRICAS MANUALES POR HOTEL COMPARTIDO:\n\n")
        n_total_nodos = len(nodes)

        for node in nodes:
            if 'Business' not in node.get('labels', []):
                continue
            if node['properties'].get('type') != 'compartido':
                continue

            nid       = node['id']
            real_id   = node['properties'].get('id', nid)
            deg       = degree[nid]
            n_interm  = sum(1 for uid in rels_por_fin.get(nid, set()) if uid in usuarios_interm_node_ids)
            ratio     = n_interm / len(usuarios_interm_node_ids) if usuarios_interm_node_ids else 0.0
            norm_deg  = deg / (n_total_nodos - 1) if n_total_nodos > 1 else 0.0

            f.write(f"  Hotel compartido real_id={real_id} (node_id={nid})\n")
            f.write(f"    degree total en subgrafo : {deg}\n")
            f.write(f"    usuarios intermedios que lo valoraron: {n_interm} / {len(usuarios_interm_node_ids)}\n")
            f.write(f"    → cf_degree_hotel              : {float(deg)}\n")
            f.write(f"    → cf_ratio_usuarios_compartidos: {ratio:.4f}\n")
            f.write(f"    → cf_norm_degree_hotel         : {norm_deg:.4f}  ({deg}/{n_total_nodos-1})\n\n")

        # Resultado real
        f.write(f"{'─'*60}\n")
        f.write("RESULTADO REAL DEL CÓDIGO:\n")
        for fila in metricas_resultado:
            f.write(f"\n  hotel_explicador={fila.get('hotel_explicador')}\n")
            for k, v in fila.items():
                if k not in ('usuario', 'hotel_recomendado', 'hotel_explicador'):
                    f.write(f"    {k}: {v}\n")

    return json_path, txt_path


# ============================================================
# FLUJO ATÓMICO KG
# ============================================================

def procesar_par_kg(
    user_id: int, hotel_rec: int,
    logger: logging.Logger,
    debug: bool = False
) -> List[Dict]:
    try:
        hoteles_historicos = get_user_interacted_hotels(user_id)
        logger.info(f"  [KG] Histórico user={user_id}: {hoteles_historicos}")
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

            if debug:
                jp, tp = guardar_debug_kg(user_id, hotel_rec, nodes_kg, rels_kg, hoteles_historicos, filas)
                logger.info(f"  [DEBUG-KG] JSON  → {jp}")
                logger.info(f"  [DEBUG-KG] Informe → {tp}")

            return filas
        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        import traceback
        logger.error(f"  [KG] Error: {e}")
        logger.error(traceback.format_exc())
        return []


# ============================================================
# FLUJO ATÓMICO CF
# ============================================================

def procesar_par_cf(
    user_id: int, hotel_rec: int,
    logger: logging.Logger,
    debug: bool = False
) -> List[Dict]:
    try:
        result_cf = get_subgraph_for_user_and_hotel(user_id, hotel_rec)

        if result_cf is None:
            logger.warning(f"  [CF] Sin patrón para user={user_id}, hotel={hotel_rec}")
            return []

        nodes_cf, rels_cf = result_cf
        logger.info(f"  [CF] Subgrafo: {len(nodes_cf)} nodos, {len(rels_cf)} relaciones")

        # TEMPORAL: contar cuántas relaciones tienen rating
        con_rating = sum(1 for r in rels_cf if r.get('properties', {}).get('rating') is not None)
        logger.info(f"  [CF] Relaciones con rating: {con_rating}/{len(rels_cf)}")

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

            if debug:
                jp, tp = guardar_debug_cf(user_id, hotel_rec, nodes_cf, rels_cf, filas)
                logger.info(f"  [DEBUG-CF] JSON  → {jp}")
                logger.info(f"  [DEBUG-CF] Informe → {tp}")

            return filas
        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"  [CF] Error: {e}")
        return []


# ============================================================
# GUARDAR CSVs
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
    if not filas:
        return

    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(filas)

    for metrica in nombres_metricas:
        if metrica not in df.columns:
            logger.warning(f"  ⚠️  '{metrica}' no encontrada, se omite")
            continue

        # Base: ordenar descendente por valor dentro de cada par (usuario, hotel_recomendado)
        df_sorted = (
            df[['usuario', 'hotel_recomendado', 'hotel_explicador', metrica]]
            .copy()
            .rename(columns={metrica: 'valor_metrica'})
            .sort_values(
                ['usuario', 'hotel_recomendado', 'valor_metrica'],
                ascending=[True, True, False]
            )
        )

        # Top-5 completo
        df_top5 = (
            df_sorted
            .groupby(['usuario', 'hotel_recomendado'], group_keys=False)
            .head(5)
            .reset_index(drop=True)
        )
        nombre = f"{prefijo}_usuario_{usuario}_{metrica}_{timestamp}.csv"
        df_top5.to_csv(output_dir / nombre, index=False, encoding='utf-8')
        logger.info(f"  💾 {nombre}  ({len(df_top5)} filas)")

        '''
        # @1 — mejor explicador por recomendación
        df_at1 = (
            df_sorted
            .groupby(['usuario', 'hotel_recomendado'], group_keys=False)
            .head(1)
            .reset_index(drop=True)
        )
        nombre_at1 = f"{prefijo}_usuario_{usuario}_{metrica}_at1_{timestamp}.csv"
        df_at1.to_csv(output_dir / nombre_at1, index=False, encoding='utf-8')
        logger.info(f"  💾 {nombre_at1}  ({len(df_at1)} filas)")

        # @3 — top-3 explicadores por recomendación
        df_at3 = (
            df_sorted
            .groupby(['usuario', 'hotel_recomendado'], group_keys=False)
            .head(3)
            .reset_index(drop=True)
        )
        nombre_at3 = f"{prefijo}_usuario_{usuario}_{metrica}_at3_{timestamp}.csv"
        df_at3.to_csv(output_dir / nombre_at3, index=False, encoding='utf-8')
        logger.info(f"  💾 {nombre_at3}  ({len(df_at3)} filas)")
        '''

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
    parser.add_argument(
        "--debug", action="store_true",
        help="Guarda JSONs de subgrafos e informes de validación en output/debug/"
    )
    parser.add_argument(
        "--hotel", type=int, default=None,
        help="Con --debug, limitar a un único hotel recomendado concreto"
    )
    args = parser.parse_args()

    logger    = setup_logging(args.modo)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    dir_kg = OUTPUT_DIR / f"metricas_grafo_conocimiento_{args.modo}"
    dir_cf = OUTPUT_DIR / f"metricas_grafo_interaccion_{args.modo}"

    logger.info("=" * 70)
    logger.info(f"PIPELINE XAI — MODO={args.modo.upper()}" + (" [DEBUG]" if args.debug else ""))
    logger.info(f"Timestamp : {timestamp}")
    logger.info(f"Métricas KG ({len(NOMBRES_METRICAS_KG)}): {NOMBRES_METRICAS_KG}")
    logger.info(f"Métricas CF ({len(NOMBRES_METRICAS_CF)}): {NOMBRES_METRICAS_CF}")
    if args.debug:
        logger.info(f"Debug dir : {DEBUG_DIR.resolve()}")
        if args.hotel:
            logger.info(f"Debug hotel filtro: {args.hotel}")
    logger.info("=" * 70)

    if not CSV_RECOMENDACIONES.exists():
        logger.error(f"❌ No existe: {CSV_RECOMENDACIONES}")
        sys.exit(1)

    df = pd.read_csv(CSV_RECOMENDACIONES)
    logger.info(f"📂 Recomendaciones: {len(df)} filas")

    if args.modo == "muestra":
        df = df[df['usuario'].isin(args.usuarios)]
        logger.info(f"🔍 Usuarios: {args.usuarios} → {len(df)} pares")

    acumulador: Dict[int, Dict] = defaultdict(lambda: {'kg': [], 'cf': []})
    errores = 0
    total   = len(df)

    for idx, row in df.iterrows():
        user_id   = int(row['usuario'])
        hotel_rec = int(row['negocio'])

        # En modo debug con --hotel, solo guardamos JSONs para ese hotel concreto
        debug_este_par = args.debug and (args.hotel is None or args.hotel == hotel_rec)

        logger.info(f"\n{'─'*50}")
        logger.info(f"Par {idx+1}/{total}: user={user_id}, hotel_rec={hotel_rec}" +
                    (" [DEBUG]" if debug_este_par else ""))
        t0 = time.time()

        try:
            filas_kg = procesar_par_kg(user_id, hotel_rec, logger, debug=debug_este_par)
            filas_cf = procesar_par_cf(user_id, hotel_rec, logger, debug=debug_este_par)

            acumulador[user_id]['kg'].extend(filas_kg)
            acumulador[user_id]['cf'].extend(filas_cf)

            logger.info(
                f"  ✅ OK ({time.time()-t0:.2f}s) "
                f"KG:{len(filas_kg)} CF:{len(filas_cf)} filas"
            )
        except Exception as e:
            logger.error(f"  ❌ Error inesperado: {e}")
            errores += 1

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
    if args.debug:
        n_debug = len(list(DEBUG_DIR.glob("*"))) if DEBUG_DIR.exists() else 0
        logger.info(f"   Ficheros debug: {n_debug}  →  {DEBUG_DIR}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()