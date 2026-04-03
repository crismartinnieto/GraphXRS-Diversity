"""
src/evaluacion/pipeline.py

Pipeline de EVALUACIÓN XAI.

El CSV de histórico es siempre el mismo (data/raw/grafo_interaccion_datos_train.csv).
Solo hay que indicar qué carpeta de algoritmos evaluar: muestra o completo.

EJECUTAR:
    # Evaluar los resultados de muestra (KG + CF):
    python src/evaluacion/pipeline.py --modo muestra

    # Evaluar los resultados completos (KG + CF):
    python src/evaluacion/pipeline.py --modo completo

    # Evaluar solo KG de muestra:
    python src/evaluacion/pipeline.py --modo muestra --fuente kg

    # Evaluar solo CF de muestra:
    python src/evaluacion/pipeline.py --modo muestra --fuente cf

    # Cutoffs personalizados:
    python src/evaluacion/pipeline.py --modo muestra --ks 1 3

SALIDA (un CSV por usuario con TODOS los algoritmos como filas):
    output/metricas_evaluacion_muestra/evaluacion_usuario_{U}_AggDiv_IXD_{timestamp}.csv
    output/metricas_evaluacion_completo/evaluacion_usuario_{U}_AggDiv_IXD_{timestamp}.csv

    Columnas:
        usuario | hotel_recomendado | algoritmo |
        AggDiv | AggDiv_norm | AggDiv@1 | AggDiv@1_norm | AggDiv@3 | AggDiv@3_norm | AggDiv@5 | AggDiv@5_norm |
        IXD | IXD@1 | IXD@3 | IXD@5 |
        historico_lista | historico_num

NOTAS SOBRE IXD:
    IXD se calcula a nivel de usuario+algoritmo (un único valor por combinación).
    Se replica en todas las filas del usuario para ese algoritmo, de modo que
    el CSV mantiene una fila por par (usuario, hotel_recomendado).
    Si el usuario solo tiene una recomendación, IXD = NaN (no definida).
"""

import sys
import argparse
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd

# ----------------------------------------------------------
# Rutas del proyecto (relativas a la raíz del proyecto)
# ----------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent   # sube: evaluacion → src → raiz

CSV_HISTORICO = PROJECT_ROOT / "data" / "raw" / "grafo_interaccion_datos_train.csv"

CARPETAS_ALGORITMOS = {
    ("kg",  "muestra"):  PROJECT_ROOT / "output" / "metricas_grafo_conocimiento_muestra",
    ("kg",  "completo"): PROJECT_ROOT / "output" / "metricas_grafo_conocimiento_completo",
    ("cf",  "muestra"):  PROJECT_ROOT / "output" / "metricas_grafo_interaccion_muestra",
    ("cf",  "completo"): PROJECT_ROOT / "output" / "metricas_grafo_interaccion_completo",
}

OUTPUT_EVAL_DIRS = {
    "muestra":  PROJECT_ROOT / "output" / "metricas_evaluacion_muestra",
    "completo": PROJECT_ROOT / "output" / "metricas_evaluacion_completo",
}

LOGS_DIR = PROJECT_ROOT / "logs"

SRC_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SRC_DIR))

from evaluacion.metricas_evaluacion import calcular_evaluacion, ESTRATEGIAS_EVALUACION


# ============================================================
# LOGGING
# ============================================================

def setup_logging(modo: str) -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file  = LOGS_DIR / f"pipeline_evaluacion_{modo}_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("pipeline_evaluacion")


# ============================================================
# HELPERS
# ============================================================

PATRONES_ALGORITMO = [
    "kg_num_propiedades_compartidas",
    "kg_ratio_propiedades_compartidas",
    "kg_peso_ponderado_perfil",
    "kg_jaccard_similarity",
    "cf_degree_hotel",
    "cf_ratio_usuarios_compartidos",
    "cf_norm_degree_hotel",
    "cf_betweenness_hotel",
]


def _inferir_nombre_algoritmo(csv_path: Path) -> str:
    stem = csv_path.stem
    for patron in PATRONES_ALGORITMO:
        if patron in stem:
            return patron
    return stem


def _inferir_usuario(csv_path: Path) -> int | None:
    stem  = csv_path.stem
    parts = stem.split("_")
    for i, part in enumerate(parts):
        if part == "usuario" and i + 1 < len(parts):
            try:
                return int(parts[i + 1])
            except ValueError:
                return None
    return None


def _recopilar_csvs(fuentes: list, modo: str, logger: logging.Logger) -> list:
    csvs = []
    for fuente in fuentes:
        carpeta = CARPETAS_ALGORITMOS.get((fuente, modo))
        if carpeta is None:
            logger.warning(f"⚠️  Combinación no reconocida: fuente={fuente}, modo={modo}")
            continue
        if not carpeta.exists():
            logger.warning(f"⚠️  Carpeta no encontrada: {carpeta}")
            continue
        encontrados = sorted(carpeta.glob("*.csv"))
        logger.info(f"📂 [{fuente.upper()} / {modo}] {carpeta.name}: {len(encontrados)} CSVs")
        csvs.extend(encontrados)
    return csvs


def _log_fila(logger: logging.Logger, fila: pd.Series, ks: List[int]) -> None:
    """Imprime en el log los valores de AggDiv e IXD para una fila."""
    vals_aggdiv = "  ".join(
        f"AggDiv@{k}={fila.get(f'AggDiv@{k}', 'N/A')} "
        f"(norm={fila.get(f'AggDiv@{k}_norm', 'N/A')})"
        for k in ks
    )
    vals_ixd = "  ".join(
        f"IXD@{k}={fila.get(f'IXD@{k}', 'N/A')}"
        for k in ks
    )
    logger.info(
        f"    usuario={int(fila['usuario'])}  "
        f"hotel_rec={int(fila['hotel_recomendado'])}  "
        f"algoritmo={fila['algoritmo']}  "
        f"AggDiv={fila.get('AggDiv')} (norm={fila.get('AggDiv_norm')})  "
        f"{vals_aggdiv}  "
        f"IXD={fila.get('IXD')}  {vals_ixd}  "
        f"hist_n={fila.get('historico_num')}"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline de evaluación XAI — AggDiv + IXD sobre rankings de explicación"
    )
    parser.add_argument(
        "--modo", choices=["muestra", "completo"], default="muestra",
        help="Qué carpeta de resultados evaluar (default: muestra)",
    )
    parser.add_argument(
        "--fuente", nargs="+", choices=["kg", "cf"], default=["kg", "cf"],
        help="Fuente(s) a evaluar: kg, cf, o ambas (default: kg cf)",
    )
    parser.add_argument(
        "--ks", nargs="+", type=int, default=[1, 3, 5],
        help="Cutoffs @k (default: 1 3 5)",
    )
    args = parser.parse_args()

    logger          = setup_logging(args.modo)
    timestamp       = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_eval_dir = OUTPUT_EVAL_DIRS[args.modo]

    logger.info("=" * 70)
    logger.info(f"PIPELINE EVALUACIÓN XAI — MODO={args.modo.upper()}  FUENTE={args.fuente}")
    logger.info(f"Histórico       : {CSV_HISTORICO}")
    logger.info(f"Cutoffs @k      : {args.ks}")
    logger.info(f"Métricas eval   : {[e.nombre() for e in ESTRATEGIAS_EVALUACION]}")
    logger.info(f"Carpeta salida  : {output_eval_dir}")
    logger.info("=" * 70)

    if not CSV_HISTORICO.exists():
        logger.error(f"❌ No se encontró el CSV de histórico: {CSV_HISTORICO}")
        sys.exit(1)

    csvs = _recopilar_csvs(args.fuente, args.modo, logger)
    if not csvs:
        logger.error("❌ No se encontraron CSVs de algoritmos para evaluar.")
        sys.exit(1)

    logger.info(f"Total CSVs a evaluar: {len(csvs)}\n")
    output_eval_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------
    # ACUMULAR filas de evaluación por usuario
    # Cada fila: (usuario, hotel_recomendado, algoritmo, AggDiv..., IXD...)
    # IXD ya viene calculada correctamente desde calcular_evaluacion(),
    # que hace su propio segundo pase interno por usuario+algoritmo.
    # -------------------------------------------------------
    filas_por_usuario: Dict[int, List[dict]] = defaultdict(list)

    for i, csv_path in enumerate(csvs, 1):
        nombre_algoritmo = _inferir_nombre_algoritmo(csv_path)
        usuario_csv      = _inferir_usuario(csv_path)

        logger.info(f"[{i}/{len(csvs)}] {csv_path.name}")
        logger.info(f"  Algoritmo detectado : {nombre_algoritmo}")
        logger.info(f"  Usuario detectado   : {usuario_csv}")

        try:
            df = calcular_evaluacion(
                csv_historico=CSV_HISTORICO,
                csv_algoritmo=csv_path,
                nombre_algoritmo=nombre_algoritmo,
                ks=args.ks,
                estrategias=ESTRATEGIAS_EVALUACION,
            )

            for _, fila in df.iterrows():
                u = int(fila["usuario"])
                filas_por_usuario[u].append(fila.to_dict())
                _log_fila(logger, fila, args.ks)

        except Exception as e:
            import traceback
            logger.error(f"  ❌ Error en {csv_path.name}: {e}")
            logger.error(traceback.format_exc())

    # -------------------------------------------------------
    # GUARDAR un CSV por usuario con todos los algoritmos
    # -------------------------------------------------------
    logger.info(f"\n{'=' * 70}")
    logger.info("GUARDANDO CSVs POR USUARIO...")
    logger.info(f"{'=' * 70}\n")

    nombre_metrica_eval = "_".join(e.nombre() for e in ESTRATEGIAS_EVALUACION)

    # Orden de columnas del CSV de salida
    columnas_base    = ["usuario", "hotel_recomendado", "algoritmo"]
    columnas_aggdiv  = (
        ["AggDiv", "AggDiv_norm"]
        + [col for k in args.ks for col in (f"AggDiv@{k}", f"AggDiv@{k}_norm")]
    )
    columnas_ixd     = ["IXD"] + [f"IXD@{k}" for k in args.ks]
    columnas_hist    = ["historico_lista", "historico_num"]
    columnas_deseado = columnas_base + columnas_aggdiv + columnas_ixd + columnas_hist

    n_guardados = 0
    for usuario, filas in sorted(filas_por_usuario.items()):
        df_usuario = pd.DataFrame(filas)

        # Aplicar orden de columnas (solo las que existan en el df)
        columnas_orden = [c for c in columnas_deseado if c in df_usuario.columns]
        df_usuario = df_usuario[columnas_orden]

        # Ordenar filas: hotel_recomendado → algoritmo
        df_usuario = df_usuario.sort_values(
            ["hotel_recomendado", "algoritmo"]
        ).reset_index(drop=True)

        nombre_salida = (
            f"evaluacion_usuario_{usuario}_{nombre_metrica_eval}_{timestamp}.csv"
        )
        ruta_salida = output_eval_dir / nombre_salida
        df_usuario.to_csv(ruta_salida, index=False, encoding="utf-8")
        n_guardados += 1

        n_pares      = df_usuario[["usuario", "hotel_recomendado"]].drop_duplicates().shape[0]
        n_algoritmos = df_usuario["algoritmo"].nunique()
        logger.info(
            f"  💾 usuario={usuario} → {nombre_salida}  "
            f"({len(df_usuario)} filas: {n_pares} hoteles_rec × {n_algoritmos} algoritmos)"
        )

        # Log detallado por fila
        for _, fila in df_usuario.iterrows():
            vals_ixd = "  ".join(f"IXD@{k}={fila.get(f'IXD@{k}', 'N/A')}" for k in args.ks)
            logger.info(
                f"       hotel_rec={int(fila['hotel_recomendado'])}  "
                f"algoritmo={fila['algoritmo']}  "
                f"AggDiv={fila.get('AggDiv')} (norm={fila.get('AggDiv_norm')})  "
                f"IXD={fila.get('IXD')}  {vals_ixd}"
            )

    logger.info(f"\n{'=' * 70}")
    logger.info("✅ EVALUACIÓN COMPLETADA")
    logger.info(f"   Usuarios procesados : {len(filas_por_usuario)}")
    logger.info(f"   CSVs generados      : {n_guardados}  →  {output_eval_dir}")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    main()