"""
src/extraccion_metricas_interaccion/calcular_interaccion.py

Calcula métricas del grafo de interacción y guarda UN CSV por métrica por usuario.

Formato nombre fichero: cf_usuario_X_nombremetrica_TIMESTAMP.csv
Formato columnas:       usuario | hotel_recomendado | hotel_compartido | valor_metrica
"""
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (
    SUBGRAFOS_INTERACCIONES,
    CSV_USUARIO_RATING_RECOMEND,
    METRICAS_INTERACCION,
    LOGS_DIR,
    MODE,
    USUARIOS_MUESTRA,
)
from métricas import (
    CentralidadStrategy,
    load_subgraph,
    build_graph_index,
    DegreeCentralidadHotelStrategy,
    RatioUsuariosCompartidosStrategy,
    NumUsuariosCompartidosStrategy,
    PesoMedioRatingHotelStrategy,
    NormDegreeCentralidadHotelStrategy,
)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "metricas_interaccion.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================
# CALCULADOR
# ============================================================

class CalculadorCentralidades:
    """
    Coordina el cálculo de múltiples estrategias sobre subgrafos de interacción.
    Mismo patrón que CalculadorMetricas (grafo conocimiento).
    """

    def __init__(self):
        self.estrategias: List[CentralidadStrategy] = []

    def agregar_estrategia(self, e: CentralidadStrategy):
        self.estrategias.append(e)

    def agregar_estrategias(self, estrategias: List[CentralidadStrategy]):
        self.estrategias.extend(estrategias)

    def limpiar_estrategias(self):
        self.estrategias = []

    def _calcular_fila(self, usuario_real_id, recommended_hotel,
                       hotel_real_id, node_id, node_info, index) -> Dict[str, Any]:
        """Calcula todas las estrategias para un hotel compartido."""
        fila = {
            'usuario':           usuario_real_id,
            'hotel_recomendado': recommended_hotel,
            'hotel_compartido':  hotel_real_id,
        }
        for estrategia in self.estrategias:
            try:
                fila[estrategia.nombre()] = estrategia.calcular(node_id, node_info, index)
            except Exception as e:
                logger.warning(f"Error en {estrategia.nombre()}: {e}")
                fila[estrategia.nombre()] = None
        return fila

    def calcular_para_subgrafo(self, json_path: Path,
                               csv_user_id, recommended_hotel) -> List[Dict]:
        """Devuelve una fila por hotel compartido válido del subgrafo."""
        nodes, relationships = load_subgraph(json_path)
        index = build_graph_index(nodes, relationships)

        (_, relaciones_por_inicio, relaciones_por_fin,
         usuario_objetivo, hotel_recomendado,
         usuarios_intermedios, hoteles_compartidos) = index

        if usuario_objetivo is None:
            logger.warning(f"  Sin usuario objetivo en {json_path.name}")
            return []

        usuario_real_id = usuario_objetivo[1]['properties'].get('id', usuario_objetivo[0])
        filas = []

        for h_id, h_info in hoteles_compartidos.items():
            hotel_real_id    = h_info['properties'].get('id', h_id)
            usuarios_que_val = sum(
                1 for uid in relaciones_por_fin.get(h_id, {})
                if uid in usuarios_intermedios
            )
            if h_info['degree'] > 0 and usuarios_que_val > 0:
                filas.append(self._calcular_fila(
                    usuario_real_id, recommended_hotel,
                    hotel_real_id, h_id, h_info, index
                ))

        return filas

    def calcular_para_usuario(self, usuario_id) -> List[Dict]:
        """Procesa todos los JSONs del usuario y devuelve lista de filas."""
        json_files = list(SUBGRAFOS_INTERACCIONES.glob(
            f"user_{usuario_id}_hotel_*_interactions.json"
        ))

        if not json_files:
            raise FileNotFoundError(
                f"No hay JSONs para usuario {usuario_id} en {SUBGRAFOS_INTERACCIONES}"
            )

        logger.info(f"  {len(json_files)} subgrafos para usuario {usuario_id}")

        todas = []
        for json_path in json_files:
            recommended_hotel = json_path.stem.split('_')[3]
            todas.extend(self.calcular_para_subgrafo(json_path, usuario_id, recommended_hotel))

        return todas


# ============================================================
# GUARDADO — un CSV por métrica por usuario
# ============================================================

def guardar_por_metrica(df_resultados: pd.DataFrame, usuario: int,
                        nombre_metrica: str, timestamp: str):
    """
    Extrae una sola métrica del DataFrame completo y guarda un CSV con 4 columnas:
        usuario | hotel_recomendado | hotel_compartido | valor_metrica

    Nombre del fichero: cf_usuario_X_nombremetrica_TIMESTAMP.csv
    """
    if nombre_metrica not in df_resultados.columns:
        logger.warning(f"  ⚠️  Columna '{nombre_metrica}' no encontrada, se omite")
        return

    df_metrica = (
        df_resultados[['usuario', 'hotel_recomendado', 'hotel_compartido', nombre_metrica]]
        .rename(columns={nombre_metrica: 'valor_metrica'})
    )

    nombre_fichero = f"cf_usuario_{usuario}_{nombre_metrica}_{timestamp}.csv"
    output_path    = METRICAS_INTERACCION / nombre_fichero
    df_metrica.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"  💾 {nombre_fichero}  ({len(df_metrica)} filas)")


# ============================================================
# MAIN
# ============================================================

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 70)
    logger.info(f"CÁLCULO MÉTRICAS INTERACCIÓN — MODE={MODE}")
    logger.info(f"Timestamp: {timestamp}")
    logger.info("=" * 70)
    logger.info(f"📂 Subgrafos: {SUBGRAFOS_INTERACCIONES}")
    logger.info(f"💾 Salida:    {METRICAS_INTERACCION}")

    if not CSV_USUARIO_RATING_RECOMEND.exists():
        logger.error(f"❌ No existe: {CSV_USUARIO_RATING_RECOMEND}")
        sys.exit(1)

    df            = pd.read_csv(CSV_USUARIO_RATING_RECOMEND)
    usuarios_todos = df['usuario'].unique()

    if MODE == "muestra":
        usuarios = [u for u in USUARIOS_MUESTRA if u in usuarios_todos]
    else:
        usuarios = [
            u for u in usuarios_todos
            if list(SUBGRAFOS_INTERACCIONES.glob(f"user_{u}_hotel_*_interactions.json"))
        ]

    logger.info(f"\n👥 Usuarios a procesar: {len(usuarios)} → {usuarios}\n")

    if not usuarios:
        logger.error("❌ Sin usuarios con subgrafos. Ejecuta antes extract_interaction_subgraphs.py")
        sys.exit(1)

    # ── Estrategias ─────────────────────────────────────────
    estrategias = [
        DegreeCentralidadHotelStrategy(),
        RatioUsuariosCompartidosStrategy(),
        NumUsuariosCompartidosStrategy(),
        PesoMedioRatingHotelStrategy(),
        NormDegreeCentralidadHotelStrategy(),
    ]

    calculador = CalculadorCentralidades()
    calculador.agregar_estrategias(estrategias)

    nombres_metricas = [e.nombre() for e in estrategias]
    logger.info(f"📐 Métricas registradas ({len(nombres_metricas)}): {nombres_metricas}\n")

    # ── Procesar cada usuario ────────────────────────────────
    for usuario in usuarios:
        logger.info(f"\n{'='*60}")
        logger.info(f"Usuario {usuario}")
        logger.info(f"{'='*60}")

        try:
            resultados    = calculador.calcular_para_usuario(usuario)
            df_resultados = pd.DataFrame(resultados)

            logger.info(f"  Combinaciones calculadas: {len(df_resultados)}")

            # Guardar un CSV por cada métrica
            for nombre_metrica in nombres_metricas:
                guardar_por_metrica(df_resultados, usuario, nombre_metrica, timestamp)

            logger.info(f"✅ Usuario {usuario}: {len(nombres_metricas)} ficheros guardados")

        except FileNotFoundError as e:
            logger.error(f"❌ Ficheros no encontrados para usuario {usuario}: {e}")
        except Exception as e:
            logger.error(f"❌ Error en usuario {usuario}: {e}")
            import traceback; traceback.print_exc()

    logger.info(f"\n{'='*70}")
    logger.info("🎉 COMPLETADO")
    logger.info(f"   Usuarios:         {len(usuarios)}")
    logger.info(f"   Métricas:         {len(nombres_metricas)}")
    logger.info(f"   Ficheros totales: {len(usuarios) * len(nombres_metricas)}")
    logger.info(f"   Resultados en:    {METRICAS_INTERACCION}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()