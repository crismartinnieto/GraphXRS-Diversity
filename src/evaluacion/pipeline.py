"""
src/evaluacion/pipeline.py

Pipeline de EVALUACIÓN XAI.

EJECUTAR:
    python src/evaluacion/pipeline.py --modo muestra
    python src/evaluacion/pipeline.py --modo completo
    python src/evaluacion/pipeline.py --modo muestra --fuente kg
    python src/evaluacion/pipeline.py --modo muestra --fuente cf
    python src/evaluacion/pipeline.py --modo muestra --ks 1 3

SALIDA — un CSV por métrica y por algoritmo:

    output/metricas_evaluacion_muestra/
        evaluacion_{algoritmo}_AggDiv_{timestamp}.csv
        evaluacion_{algoritmo}_IXD_{timestamp}.csv
        evaluacion_{algoritmo}_MIL_{timestamp}.csv
        evaluacion_{algoritmo}_ECS_{timestamp}.csv

    Columnas:

        AggDiv  (granularidad usuario):
            usuario | historico_num | algoritmo | AggDiv | AggDiv@1 | AggDiv@3 | AggDiv@5

        IXD  (granularidad usuario):
            usuario | historico_num | algoritmo | IXD | IXD@1 | IXD@3 | IXD@5

        MIL  (granularidad sistema — UNA sola fila por algoritmo):
            algoritmo | MIL | MIL@1 | MIL@3 | MIL@5

        ECS  (granularidad hotel_recomendado — una fila por h_rec con ≥2 usuarios):
            hotel_recomendado | n_usuarios | algoritmo | ECS | ECS@1 | ECS@3 | ECS@5

FLUJO:
    1. CSV a CSV → calcular AggDiv e IXD por usuario, acumular df crudo.
    2. Tras acumular todos los CSVs de un algoritmo:
       → calcular MIL  con el DataFrame completo (granularidad sistema).
       → calcular ECS  con el DataFrame completo (granularidad hotel).
    3. Guardar un CSV por algoritmo y métrica.
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# ----------------------------------------------------------
# Rutas del proyecto
# ----------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent

CSV_HISTORICO = PROJECT_ROOT / "data" / "raw" / "grafo_interaccion_datos_train.csv"

CARPETAS_ALGORITMOS = {
    ("kg",  "muestra"):  PROJECT_ROOT / "output" / "metricas_grafo_conocimiento_muestra",
    ("kg",  "completo"): PROJECT_ROOT / "output" / "metricas_grafo_conocimiento_completo",
    ("cf",  "muestra"):  PROJECT_ROOT / "output" / "metricas_grafo_interaccion_muestra",
    ("cf",  "completo"): PROJECT_ROOT / "output" / "metricas_grafo_interaccion_completo",
    ("cf",  "semi"):     PROJECT_ROOT / "output" / "metricas_grafo_interaccion_semi",
    ("kg",  "semi"):     PROJECT_ROOT / "output" / "metricas_grafo_conocimiento_semi",
}

OUTPUT_EVAL_DIRS = {
    "muestra":  PROJECT_ROOT / "output" / "metricas_evaluacion_muestra",
    "completo": PROJECT_ROOT / "output" / "metricas_evaluacion_completo",
    "semi":     PROJECT_ROOT / "output" / "metricas_evaluacion_semi",
}

LOGS_DIR = PROJECT_ROOT / "logs"

SRC_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SRC_DIR))

from evaluacion.metricas_evaluacion import (
    calcular_evaluacion_usuario,
    ESTRATEGIAS_EVALUACION,
    MILStrategy,
    ECSStrategy,
    MetricaEvaluacionStrategy,
)


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

ESTRATEGIAS_POR_NOMBRE: Dict[str, MetricaEvaluacionStrategy] = {
    e.nombre(): e for e in ESTRATEGIAS_EVALUACION
}

ESTRATEGIAS_USUARIO = [e for e in ESTRATEGIAS_EVALUACION if e.granularidad() == "usuario"]
ESTRATEGIAS_SISTEMA = [e for e in ESTRATEGIAS_EVALUACION if e.granularidad() == "sistema"]
ESTRATEGIAS_HOTEL   = [e for e in ESTRATEGIAS_EVALUACION if e.granularidad() == "hotel"]


def _inferir_nombre_algoritmo(csv_path: Path) -> str:
    stem = csv_path.stem
    for patron in PATRONES_ALGORITMO:
        if patron in stem:
            return patron
    return stem


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


def _cargar_historico(logger: logging.Logger) -> Dict[int, List[int]]:
    df_hist = pd.read_csv(CSV_HISTORICO)
    df_hist.columns = [c.strip().lower() for c in df_hist.columns]
    if "user_id" in df_hist.columns and "business_id" in df_hist.columns:
        df_hist = df_hist.rename(columns={"user_id": "usuario", "business_id": "hotel"})
    return (
        df_hist.groupby("usuario")["hotel"]
        .apply(lambda s: sorted(s.astype(int).tolist()))
        .to_dict()
    )


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Pipeline de evaluación XAI — AggDiv + IXD + MIL + ECS"
    )
    parser.add_argument("--modo", choices=["muestra", "completo", "semi"], default="muestra")
    parser.add_argument("--fuente", nargs="+", choices=["kg", "cf"], default=["kg", "cf"])
    parser.add_argument("--ks", nargs="+", type=int, default=[1, 3, 5])
    # En modo muestra solo hay 2 usuarios → relajamos el umbral mínimo a 1
    # para que ECS genere una fila por h_rec con ≥1 usuario (útil para debug).
    # En modo completo se usa 2 (valor semántico real).
    parser.add_argument(
        "--ecs-min-usuarios", type=int, default=None,
        help=(
            "Nº mínimo de usuarios que deben haber recibido un hotel_recomendado "
            "para que ECS lo incluya. Por defecto: 1 en modo muestra, 2 en otros modos."
        )
    )
    args = parser.parse_args()

    # Umbral ECS: en muestra usamos 1 (permite ver resultados aunque los 2 usuarios
    # no compartan hoteles recomendados); en completo/semi usamos 2 (semántica real).
    if args.ecs_min_usuarios is not None:
        ecs_min_usuarios = args.ecs_min_usuarios
    else:
        ecs_min_usuarios = 1 if args.modo == "muestra" else 2

    logger          = setup_logging(args.modo)
    timestamp       = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_eval_dir = OUTPUT_EVAL_DIRS[args.modo]

    logger.info("=" * 70)
    logger.info(f"PIPELINE EVALUACIÓN XAI — MODO={args.modo.upper()}  FUENTE={args.fuente}")
    logger.info(f"Histórico      : {CSV_HISTORICO}")
    logger.info(f"Cutoffs @k     : {args.ks}")
    logger.info(f"Métricas eval  : {[e.nombre() for e in ESTRATEGIAS_EVALUACION]}")
    logger.info(f"ECS min_usuarios: {ecs_min_usuarios}")
    logger.info(f"Carpeta salida : {output_eval_dir}")
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

    historico_por_usuario = _cargar_historico(logger)

    # ----------------------------------------------------------
    # Estructuras de acumulación
    # ----------------------------------------------------------
    acumulado_usuario: Dict[str, Dict[str, List[pd.DataFrame]]] = {}
    acumulado_alg_raw: Dict[str, List[pd.DataFrame]] = {}

    # -------------------------------------------------------
    # PASO 1 — CSV a CSV: calcular métricas de usuario
    # -------------------------------------------------------
    for i, csv_path in enumerate(csvs, 1):
        nombre_algoritmo = _inferir_nombre_algoritmo(csv_path)
        logger.info(f"[{i}/{len(csvs)}] {csv_path.name}  →  algoritmo: {nombre_algoritmo}")

        if nombre_algoritmo not in acumulado_usuario:
            acumulado_usuario[nombre_algoritmo] = {
                e.nombre(): [] for e in ESTRATEGIAS_USUARIO
            }
            acumulado_alg_raw[nombre_algoritmo] = []

        try:
            df_raw = pd.read_csv(csv_path)
            df_raw = df_raw.sort_values(
                ["usuario", "hotel_recomendado", "valor_metrica"],
                ascending=[True, True, False],
            ).reset_index(drop=True)
            acumulado_alg_raw[nombre_algoritmo].append(df_raw)

            dfs_usuario = calcular_evaluacion_usuario(
                csv_historico=CSV_HISTORICO,
                csv_algoritmo=csv_path,
                nombre_algoritmo=nombre_algoritmo,
                ks=args.ks,
                estrategias=ESTRATEGIAS_USUARIO,
            )

            for nombre_metrica, df in dfs_usuario.items():
                if df.empty:
                    continue
                acumulado_usuario[nombre_algoritmo][nombre_metrica].append(df)
                estrategia = ESTRATEGIAS_POR_NOMBRE[nombre_metrica]
                for _, fila in df.iterrows():
                    logger.info(
                        f"    usuario={int(fila['usuario'])}  "
                        f"algoritmo={fila['algoritmo']}  "
                        + estrategia.log_fila(fila, args.ks)
                    )

        except Exception as e:
            import traceback
            logger.error(f"  ❌ Error en {csv_path.name}: {e}")
            logger.error(traceback.format_exc())

    # -------------------------------------------------------
    # PASO 2 — Calcular MIL (sistema) y ECS (hotel)
    # -------------------------------------------------------
    logger.info(f"\n{'=' * 70}")
    logger.info("CALCULANDO MIL (granularidad sistema)...")
    logger.info(f"{'=' * 70}\n")

    df_hist_global = pd.read_csv(CSV_HISTORICO)
    df_hist_global.columns = [c.strip().lower() for c in df_hist_global.columns]
    if "user_id" in df_hist_global.columns:
        df_hist_global = df_hist_global.rename(
            columns={"user_id": "usuario", "business_id": "hotel"}
        )
    contexto_global: Dict[str, Any] = {
        "freq_explicador":  df_hist_global.groupby("hotel")["usuario"].nunique().to_dict(),
        "n_usuarios_total": df_hist_global["usuario"].nunique(),
    }

    mil_strategy = next(
        (e for e in ESTRATEGIAS_SISTEMA if isinstance(e, MILStrategy)), None
    )
    ecs_strategy = next(
        (e for e in ESTRATEGIAS_HOTEL if isinstance(e, ECSStrategy)), None
    )

    cols_mil = mil_strategy.columnas_salida(args.ks) if mil_strategy else []
    cols_ecs = ecs_strategy.columnas_salida(args.ks) if ecs_strategy else []

    acumulado_sistema: Dict[str, pd.DataFrame] = {}
    acumulado_hotel:   Dict[str, pd.DataFrame] = {}

    for nombre_algoritmo, lista_raw in acumulado_alg_raw.items():
        if not lista_raw:
            continue

        df_completo = pd.concat(lista_raw, ignore_index=True)
        n_usuarios  = df_completo["usuario"].nunique()
        n_h_rec     = df_completo["hotel_recomendado"].nunique()

        logger.info(
            f"  MIL [{nombre_algoritmo}]: {n_usuarios} usuarios en el df acumulado"
        )

        # --- MIL ---
        if mil_strategy:
            valores_mil = mil_strategy.calcular_sistema(
                df_completo, historico_por_usuario, args.ks, contexto_global
            )
            if valores_mil is not None:
                fila_mil = {"algoritmo": nombre_algoritmo}
                fila_mil.update(valores_mil)
                acumulado_sistema[nombre_algoritmo] = pd.DataFrame(
                    [fila_mil], columns=["algoritmo"] + cols_mil
                )
                logger.info(
                    "    " + mil_strategy.log_fila(pd.Series(fila_mil), args.ks)
                )

        # --- ECS ---
        if ecs_strategy:
            # Diagnóstico: cuántos h_rec tienen ≥ ecs_min_usuarios usuarios
            conteo_h_rec = (
                df_completo.groupby("hotel_recomendado")["usuario"]
                .nunique()
            )
            elegibles = (conteo_h_rec >= ecs_min_usuarios).sum()
            logger.info(
                f"  ECS [{nombre_algoritmo}]: {n_h_rec} hoteles recomendados distintos, "
                f"{elegibles} con ≥{ecs_min_usuarios} usuario(s) → calculando ECS..."
            )

            if elegibles == 0:
                logger.warning(
                    f"  ⚠️  ECS [{nombre_algoritmo}]: ningún hotel_recomendado tiene "
                    f"≥{ecs_min_usuarios} usuarios. No se generará CSV de ECS. "
                    f"(En modo muestra esto es normal si los {n_usuarios} usuarios "
                    f"no comparten hoteles recomendados; prueba con --ecs-min-usuarios 1)"
                )
                continue

            df_ecs = ecs_strategy.calcular_hotel(
                df_completo, args.ks, contexto_global,
                min_usuarios=ecs_min_usuarios,
            )
            if df_ecs is not None and not df_ecs.empty:
                df_ecs.insert(
                    df_ecs.columns.get_loc("n_usuarios") + 1,
                    "algoritmo", nombre_algoritmo
                )
                acumulado_hotel[nombre_algoritmo] = df_ecs

                ecs_medio = df_ecs["ECS"].mean()
                logger.info(
                    f"    ECS → {len(df_ecs)} hoteles recomendados con ≥{ecs_min_usuarios} "
                    f"usuario(s)  |  ECS_medio={round(ecs_medio, 6)}"
                )
                for _, fila in df_ecs.head(5).iterrows():
                    logger.info("      " + ecs_strategy.log_fila(fila, args.ks))
            else:
                logger.warning(
                    f"  ⚠️  ECS [{nombre_algoritmo}]: calcular_hotel() devolvió DataFrame "
                    f"vacío pese a {elegibles} hoteles elegibles. Revisar datos."
                )

    # -------------------------------------------------------
    # PASO 3 — Guardar CSVs
    # -------------------------------------------------------
    logger.info(f"\n{'=' * 70}")
    logger.info("GUARDANDO CSVs POR ALGORITMO Y MÉTRICA...")
    logger.info(f"{'=' * 70}\n")

    n_guardados = 0

    # Métricas de usuario (AggDiv, IXD)
    for nombre_algoritmo, metricas_dfs in sorted(acumulado_usuario.items()):
        for estrategia in ESTRATEGIAS_USUARIO:
            nombre_metrica = estrategia.nombre()
            lista_dfs = metricas_dfs.get(nombre_metrica, [])
            if not lista_dfs:
                logger.warning(
                    f"  ⚠️  Sin datos: algoritmo={nombre_algoritmo} metrica={nombre_metrica}"
                )
                continue

            df_final = (
                pd.concat(lista_dfs, ignore_index=True)
                .sort_values("usuario")
                .reset_index(drop=True)
            )
            nombre_salida = (
                f"evaluacion_{nombre_algoritmo}_{nombre_metrica}_{timestamp}.csv"
            )
            df_final.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
            n_guardados += 1
            logger.info(f"  💾 {nombre_salida}  ({len(df_final)} usuarios)")

    # MIL (1 fila por algoritmo)
    for nombre_algoritmo, df_mil in sorted(acumulado_sistema.items()):
        nombre_salida = f"evaluacion_{nombre_algoritmo}_MIL_{timestamp}.csv"
        df_mil.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
        n_guardados += 1
        logger.info(f"  💾 {nombre_salida}  (1 fila — sistema completo)")

    # ECS (1 fila por hotel_recomendado con ≥ ecs_min_usuarios)
    for nombre_algoritmo, df_ecs in sorted(acumulado_hotel.items()):
        nombre_salida = f"evaluacion_{nombre_algoritmo}_ECS_{timestamp}.csv"
        df_ecs.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
        n_guardados += 1
        logger.info(
            f"  💾 {nombre_salida}  ({len(df_ecs)} hoteles recomendados)"
        )

    nombres_metricas = [e.nombre() for e in ESTRATEGIAS_EVALUACION]
    logger.info(f"\n{'=' * 70}")
    logger.info("✅ EVALUACIÓN COMPLETADA")
    logger.info(f"   Métricas calculadas  : {nombres_metricas}")
    logger.info(f"   Algoritmos procesados: {len(acumulado_usuario)}")
    logger.info(f"   CSVs generados       : {n_guardados}  →  {output_eval_dir}")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    main()