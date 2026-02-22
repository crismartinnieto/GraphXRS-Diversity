"""
src/extraccion_metricas_conocimiento/calcular.py
Calcula todas las métricas de explicabilidad para cada usuario.
Lee explicaciones desde data/ y guarda resultados en output/.
"""
import sys
import logging
from pathlib import Path

# Añadir src/ al path para importar config y métricas del mismo módulo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    CSV_USUARIO_RATING_RECOMEND,
    EXPLICACIONES_HISTORICO,
    EXPLICACIONES_HISTORICO_Y_REC,
    METRICAS_CONOCIMIENTO,
    LOGS_DIR,
    MODE
)

import pandas as pd
from metricas import (
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
    RiquezaExplicativaStrategy
)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "metricas.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# MAIN
# ============================================================

def main():
    logger.info("=" * 70)
    logger.info(f"CÁLCULO DE MÉTRICAS — MODE={MODE}")
    logger.info("=" * 70)
    logger.info(f"📂 Explicaciones his+rec: {EXPLICACIONES_HISTORICO_Y_REC}")
    logger.info(f"📂 Explicaciones hist:    {EXPLICACIONES_HISTORICO}")
    logger.info(f"💾 Salida métricas:       {METRICAS_CONOCIMIENTO}")

    # Verificar CSV de recomendaciones
    if not CSV_USUARIO_RATING_RECOMEND.exists():
        logger.error(f"❌ No existe: {CSV_USUARIO_RATING_RECOMEND}")
        sys.exit(1)

    df_recomend = pd.read_csv(CSV_USUARIO_RATING_RECOMEND)
    logger.info(f"\n📊 Recomendaciones cargadas: {len(df_recomend)} filas")

    usuarios_recomend = df_recomend['usuario'].unique()
    logger.info(f"   Usuarios totales en CSV: {len(usuarios_recomend)}")

    # Filtrar solo usuarios que tienen explicaciones generadas
    usuarios_con_explicaciones = [
        u for u in usuarios_recomend
        if (EXPLICACIONES_HISTORICO_Y_REC / f"explicaciones_usuario_{u}_hotel_his_y_rec.csv").exists()
    ]
    usuarios = sorted(usuarios_con_explicaciones)
    logger.info(f"   Usuarios con explicaciones: {len(usuarios)} → {usuarios}\n")

    if not usuarios:
        logger.error(f"❌ No hay usuarios con explicaciones en {EXPLICACIONES_HISTORICO_Y_REC}")
        logger.error("   Ejecuta primero crear_explicaciones.py")
        sys.exit(1)

    # Configurar calculador con todas las estrategias
    calculador = CalculadorMetricas(
        explicaciones_hist_dir=EXPLICACIONES_HISTORICO,
        explicaciones_histrec_dir=EXPLICACIONES_HISTORICO_Y_REC
    )

    calculador.agregar_estrategias([
        # Cobertura
        PropiedadesCompartidasStrategy(),
        RatioPropiedadesCompartidasStrategy(),
        CoberturaTiposPropiedadesStrategy(),
        # Ranking
        PrecisionAtKStrategy(k=5),
        RecallAtKStrategy(k=5),
        F1AtKStrategy(k=5),
        NDCGStrategy(k=5),
        MRRStrategy(),
        HitRateStrategy(),
        MAPStrategy(),
        # Diversidad y novedad
        DiversidadTiposStrategy(),
        NovedadPropiedadesStrategy(threshold=2),
        SerendipiaStrategy(),
        # Consistencia y fidelidad
        ConsistenciaTiposStrategy(),
        PesoPonderadoPerfilStrategy(),
        SimilaridadJaccardStrategy(),
        # Balance y distribución
        BalanceTiposPropiedadesStrategy(),
        RiquezaExplicativaStrategy()
    ])

    # Procesar cada usuario
    for usuario in usuarios:
        logger.info(f"\n{'='*60}")
        logger.info(f"Procesando Usuario {usuario}")
        logger.info(f"{'='*60}")

        try:
            resultados = calculador.calcular_para_usuario(usuario)
            df_resultados = pd.DataFrame(resultados)

            output_file = METRICAS_CONOCIMIENTO / f"metricas_completas_usuario_{usuario}.csv"
            df_resultados.to_csv(output_file, index=False, encoding='utf-8')

            logger.info(f"✅ Guardado: {output_file.name}")
            logger.info(f"   Filas: {len(df_resultados)} | Columnas: {len(df_resultados.columns)}")
            logger.info(f"   Métricas calculadas: {len(calculador.estrategias)}")

        except FileNotFoundError as e:
            logger.error(f"❌ Archivos no encontrados para usuario {usuario}: {e}")
        except Exception as e:
            logger.error(f"❌ Error en usuario {usuario}: {e}")
            import traceback
            traceback.print_exc()

    logger.info(f"\n{'='*70}")
    logger.info("🎉 PROCESO COMPLETADO")
    logger.info(f"   Usuarios procesados: {len(usuarios)}")
    logger.info(f"   Métricas por combinación: {len(calculador.estrategias)}")
    logger.info(f"   Resultados en: {METRICAS_CONOCIMIENTO}")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()