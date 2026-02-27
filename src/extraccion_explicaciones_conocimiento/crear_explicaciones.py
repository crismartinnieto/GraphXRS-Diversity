"""
src/extraccion_explicaciones_conocimiento/crear_explicaciones.py
Lee los JSON de subgrafos y genera dos tipos de CSV por usuario:
  - explicaciones_usuario_X_hotel_his.csv          → históricos
  - explicaciones_usuario_X_hotel_his_y_rec.csv    → comparación histórico vs recomendado
"""
import json
import sys
import logging
from pathlib import Path
from collections import defaultdict

import pandas as pd

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

# Añadir src/ al path para importar config
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (
    SUBGRAFOS_CONOCIMIENTO,
    EXPLICACIONES_HISTORICO,
    EXPLICACIONES_HISTORICO_Y_REC,
    LOGS_DIR,
    MODE
)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "explicaciones.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# FUNCIONES DE EXTRACCIÓN
# ============================================================

def extraer_propiedades_hotel(nodes, relationships, hotel_node_id):
    """Extrae las propiedades de un hotel dado su ID de nodo."""
    propiedades = set()
    for rel in relationships:
        if rel['start_node'] == hotel_node_id:
            rel_type = rel.get('properties', {}).get('type')
            for node in nodes:
                if node['id'] == rel['end_node']:
                    if 'name' in node['properties']:
                        propiedades.add((node['properties']['name'], rel_type))
                    break
    return propiedades


def procesar_subgrafo(json_path):
    """
    Procesa un JSON de subgrafo y devuelve:
      (usuario_id, hotel_rec_dict, lista_hoteles_historicos)
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes         = data['nodes']
    relationships = data['relationships']

    # Formato nombre: user_X_hotel_Y.json
    parts            = json_path.stem.split('_')   # stem = nombre sin extensión
    usuario_id       = parts[1]
    hotel_rec_id_str = parts[3]

    hoteles = [n for n in nodes if 'Business' in n['labels']]

    hotel_rec         = None
    hoteles_historicos = []

    for hotel in hoteles:
        hotel_id_prop = hotel['properties'].get('id')
        if hotel_id_prop == hotel_rec_id_str:
            hotel_rec = {
                'id':          hotel_id_prop,
                'propiedades': extraer_propiedades_hotel(nodes, relationships, hotel['id'])
            }
        else:
            hoteles_historicos.append({
                'id':          hotel_id_prop,
                'propiedades': extraer_propiedades_hotel(nodes, relationships, hotel['id'])
            })

    return usuario_id, hotel_rec, hoteles_historicos


# ============================================================
# FUNCIONES DE GENERACIÓN DE CSVs
# ============================================================

def crear_csv_comparacion(datos_usuario, usuario_id, output_path):
    """CSV: comparación entre cada hotel histórico y el recomendado."""
    filas = []
    for _, hotel_rec, hoteles_hist in datos_usuario:
        if hotel_rec is None:
            continue
        for hotel_hist in hoteles_hist:
            props_compartidas = hotel_rec['propiedades'].intersection(hotel_hist['propiedades'])
            filas.append({
                'usuario':                    usuario_id,
                'hotel_recomendado':          hotel_rec['id'],
                'hotel_historico':            hotel_hist['id'],
                'num_propiedades_compartidas': len(props_compartidas),
                'propiedades_compartidas':    list(sorted(props_compartidas))
            })

    df = pd.DataFrame(filas)
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"  ✓ CSV comparación: {output_path.name} ({len(df)} registros)")
    return len(df)


def crear_csv_historicos(datos_usuario, usuario_id, output_path):
    """CSV: propiedades de cada hotel histórico del usuario (sin duplicados)."""
    hoteles_unicos = {}
    for _, hotel_rec, hoteles_hist in datos_usuario:
        for hotel_hist in hoteles_hist:
            hotel_id = hotel_hist['id']
            if hotel_id not in hoteles_unicos:
                hoteles_unicos[hotel_id] = {
                    'usuario':          usuario_id,
                    'hotel_historico':  hotel_id,
                    'num_propiedades':  len(hotel_hist['propiedades']),
                    'propiedades':      list(sorted(hotel_hist['propiedades']))
                }

    df = pd.DataFrame(list(hoteles_unicos.values()))
    df.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"  ✓ CSV históricos:  {output_path.name} ({len(df)} registros)")
    return len(df)


# ============================================================
# MAIN
# ============================================================

def main():
    logger.info("=" * 70)
    logger.info(f"GENERACIÓN DE EXPLICACIONES — MODE={MODE}")
    logger.info("=" * 70)
    logger.info(f"📂 Entrada (subgrafos): {SUBGRAFOS_CONOCIMIENTO}")
    logger.info(f"💾 Salida históricos:   {EXPLICACIONES_HISTORICO}")
    logger.info(f"💾 Salida his+rec:      {EXPLICACIONES_HISTORICO_Y_REC}")

    # Verificar directorio de entrada
    if not SUBGRAFOS_CONOCIMIENTO.exists():
        logger.error(f"❌ No existe el directorio de subgrafos: {SUBGRAFOS_CONOCIMIENTO}")
        return

    json_files = list(SUBGRAFOS_CONOCIMIENTO.glob('*.json'))
    logger.info(f"\n📊 JSONs encontrados: {len(json_files)}")

    if not json_files:
        logger.error("❌ No hay archivos JSON. Ejecuta primero main_user_subgraph.py")
        return

    # Procesar JSONs
    datos_por_usuario = defaultdict(list)
    procesados = 0
    errores    = 0

    for json_file in json_files:
        try:
            usuario_id, hotel_rec, hoteles_hist = procesar_subgrafo(json_file)
            datos_por_usuario[usuario_id].append((usuario_id, hotel_rec, hoteles_hist))
            logger.info(f"  ✓ {json_file.name} → usuario {usuario_id}")
            procesados += 1
        except Exception as e:
            logger.error(f"  ✗ {json_file.name}: {e}")
            errores += 1

    logger.info(f"\n📈 Procesados: {procesados} | Errores: {errores}")
    logger.info(f"👥 Usuarios únicos: {len(datos_por_usuario)}")

    if not datos_por_usuario:
        logger.error("❌ Sin datos procesados. Revisa la estructura de los JSON.")
        return

    # Generar CSVs por usuario
    logger.info("\n" + "=" * 70)
    logger.info("GENERANDO CSVs...")
    logger.info("=" * 70)

    total_comp = 0
    total_hist = 0

    for usuario_id, datos_usuario in datos_por_usuario.items():
        logger.info(f"\n👤 Usuario {usuario_id}:")

        output_comp = EXPLICACIONES_HISTORICO_Y_REC / f"explicaciones_usuario_{usuario_id}_hotel_his_y_rec.csv"
        output_hist = EXPLICACIONES_HISTORICO       / f"explicaciones_usuario_{usuario_id}_hotel_his.csv"

        total_comp += crear_csv_comparacion(datos_usuario, usuario_id, output_comp)
        total_hist += crear_csv_historicos(datos_usuario,  usuario_id, output_hist)

    logger.info("\n" + "=" * 70)
    logger.info("✅ PROCESO COMPLETADO")
    logger.info(f"   Registros comparación: {total_comp}")
    logger.info(f"   Registros históricos:  {total_hist}")
    logger.info(f"   Usuarios procesados:   {len(datos_por_usuario)}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()