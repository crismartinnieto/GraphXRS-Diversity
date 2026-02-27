"""
src/extraccion_metricas_conocimiento/calcular.py

Calcula métricas del grafo de conocimiento y guarda UN CSV por métrica por usuario.

Formato nombre fichero: kg_usuario_X_nombremetrica_TIMESTAMP.csv
Formato columnas:       usuario | hotel_recomendado | hotel_compartido | valor_metrica
"""
import sys
import logging
from datetime import datetime
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config_mode import (
    CSV_USUARIO_RATING_RECOMEND,
    EXPLICACIONES_HISTORICO,
    EXPLICACIONES_HISTORICO_Y_REC,
    METRICAS_CONOCIMIENTO,
    LOGS_DIR,
    MODE,
)

import pandas as pd
from métricas import (
    CalculadorMetricas,
    PropiedadesCompartidasStrategy,
    RatioPropiedadesCompartidasStrategy,
    CoberturaTiposPropiedadesStrategy,
    PrecisionAtKStrategy,
    RecallAtKStrategy,
    F1AtKStrategy,
    NDCGStrategy,
    MRRStrategy,
    HitRateStrategy,
    MAPStrategy,
    DiversidadTiposStrategy,
    NovedadPropiedadesStrategy,
    SerendipiaStrategy,
    ConsistenciaTiposStrategy,
    PesoPonderadoPerfilStrategy,
    SimilaridadJaccardStrategy,
    BalanceTiposPropiedadesStrategy,
    RiquezaExplicativaStrategy,
)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "metricas_conocimiento.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================
# GUARDADO — un CSV por métrica por usuario
# ============================================================

def guardar_por_metrica(df_resultados: pd.DataFrame, usuario: int,
                        nombre_metrica: str, timestamp: str):
    """
    Recibe el DataFrame completo de resultados y extrae una sola métrica,
    guardando un CSV con exactamente 4 columnas:
        usuario | hotel_recomendado | hotel_compartido | valor_metrica

    Nombre del fichero: kg_usuario_X_nombremetrica_TIMESTAMP.csv
    """
    columnas_id   = ['usuario', 'hotel_recomendado', 'hotel_historico']
    columna_valor = nombre_metrica

    if columna_valor not in df_resultados.columns:
        logger.warning(f"  ⚠️  Columna '{columna_valor}' no encontrada, se omite")
        return

    df_metrica = (
        df_resultados[columnas_id + [columna_valor]]
        .rename(columns={
            'hotel_historico': 'hotel_compartido',   # renombrar para homogeneizar
            columna_valor:     'valor_metrica',
        })
    )

    nombre_fichero = f"kg_usuario_{usuario}_{nombre_metrica}_{timestamp}.csv"
    output_path    = METRICAS_CONOCIMIENTO / nombre_fichero
    df_metrica.to_csv(output_path, index=False, encoding='utf-8')
    logger.info(f"  💾 {nombre_fichero}  ({len(df_metrica)} filas)")


# ============================================================
# MAIN
# ============================================================

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 70)
    logger.info(f"CÁLCULO MÉTRICAS CONOCIMIENTO — MODE={MODE}")
    logger.info(f"Timestamp: {timestamp}")
    logger.info("=" * 70)
    logger.info(f"📂 Explicaciones his+rec: {EXPLICACIONES_HISTORICO_Y_REC}")
    logger.info(f"📂 Explicaciones hist:    {EXPLICACIONES_HISTORICO}")
    logger.info(f"💾 Salida:                {METRICAS_CONOCIMIENTO}")

    if not CSV_USUARIO_RATING_RECOMEND.exists():
        logger.error(f"❌ No existe: {CSV_USUARIO_RATING_RECOMEND}")
        sys.exit(1)

    df_recomend = pd.read_csv(CSV_USUARIO_RATING_RECOMEND)
    usuarios_recomend = df_recomend['usuario'].unique()

    usuarios = sorted([
        u for u in usuarios_recomend
        if (EXPLICACIONES_HISTORICO_Y_REC / f"explicaciones_usuario_{u}_hotel_his_y_rec.csv").exists()
    ])

    logger.info(f"\n👥 Usuarios con explicaciones: {len(usuarios)} → {usuarios}\n")

    if not usuarios:
        logger.error(f"❌ Sin explicaciones en {EXPLICACIONES_HISTORICO_Y_REC}")
        logger.error("   Ejecuta primero crear_explicaciones.py")
        sys.exit(1)

    # ── Estrategias ─────────────────────────────────────────
    estrategias = [
        PropiedadesCompartidasStrategy(),
        RatioPropiedadesCompartidasStrategy(),
        CoberturaTiposPropiedadesStrategy(),
        PrecisionAtKStrategy(k=5),
        RecallAtKStrategy(k=5),
        F1AtKStrategy(k=5),
        NDCGStrategy(k=5),
        MRRStrategy(),
        HitRateStrategy(),
        MAPStrategy(),
        DiversidadTiposStrategy(),
        NovedadPropiedadesStrategy(threshold=2),
        SerendipiaStrategy(),
        ConsistenciaTiposStrategy(),
        PesoPonderadoPerfilStrategy(),
        SimilaridadJaccardStrategy(),
        BalanceTiposPropiedadesStrategy(),
        RiquezaExplicativaStrategy(),
    ]

    calculador = CalculadorMetricas()
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
    logger.info(f"   Resultados en:    {METRICAS_CONOCIMIENTO}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()