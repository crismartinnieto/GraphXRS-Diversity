"""
src/evaluacion/pipeline.py

Pipeline de EVALUACIÓN XAI — AggDiv + IXD + MIL + ECS

EJECUTAR:
    python src/evaluacion/pipeline.py --modo muestra
    python src/evaluacion/pipeline.py --modo semi
    python src/evaluacion/pipeline.py --modo completo
    python src/evaluacion/pipeline.py --modo semi --fuente cf
    python src/evaluacion/pipeline.py --modo semi --ecs-min-usuarios 2
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# ----------------------------------------------------------
# Rutas del proyecto
# ----------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent.parent

CSV_HISTORICO = PROJECT_ROOT / "data" / "raw" / "grafo_interaccion_datos_train.csv"

OUTPUT_ROOT = PROJECT_ROOT / "output"

CARPETAS_POR_FUENTE = {
    "kg": "metricas_grafo_conocimiento_{modo}",
    "cf": "metricas_grafo_interaccion_{modo}",
}

CARPETAS_LEGACY_ALGORITMOS = {
    ("kg", "muestra"):  OUTPUT_ROOT / "metricas_grafo_conocimiento_muestra",
    ("kg", "completo"): OUTPUT_ROOT / "metricas_grafo_conocimiento_completo",
    ("kg", "semi"):     OUTPUT_ROOT / "metricas_grafo_conocimiento_semi",
    ("cf", "muestra"):  OUTPUT_ROOT / "metricas_grafo_interaccion_muestra",
    ("cf", "completo"): OUTPUT_ROOT / "metricas_grafo_interaccion_completo",
    ("cf", "semi"):     OUTPUT_ROOT / "metricas_grafo_interaccion_semi",
}

OUTPUT_EVAL_LEGACY_DIRS = {
    "muestra":  OUTPUT_ROOT / "metricas_evaluacion_muestra",
    "completo": OUTPUT_ROOT / "metricas_evaluacion_completo",
    "semi":     OUTPUT_ROOT / "metricas_evaluacion_semi",
}

CARPETAS_ALGORITMOS = CARPETAS_LEGACY_ALGORITMOS
OUTPUT_EVAL_DIRS = OUTPUT_EVAL_LEGACY_DIRS

LOGS_DIR = PROJECT_ROOT / "logs"

SRC_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SRC_DIR))

from evaluacion.metricas_evaluacion import (
    cargar_historico,
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
    log_file = LOGS_DIR / f"pipeline_evaluacion_{modo}_{timestamp}.log"
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


def _es_carpeta_modelo(carpeta: Path, fuentes: list, modo: str) -> bool:
    if not carpeta.is_dir():
        return False
    for fuente in fuentes:
        nombre_carpeta = CARPETAS_POR_FUENTE[fuente].format(modo=modo)
        if (carpeta / nombre_carpeta).exists():
            return True
    return False


def _descubrir_modelos(
    output_root: Path,
    fuentes: list,
    modo: str,
    modelos: Optional[List[str]],
    logger: logging.Logger,
) -> List[Tuple[str, Path, bool]]:
    if modelos:
        return [(modelo, output_root / modelo, False) for modelo in modelos]

    modelos_detectados = []
    if output_root.exists():
        modelos_detectados = [
            (carpeta.name, carpeta, False)
            for carpeta in sorted(output_root.iterdir())
            if _es_carpeta_modelo(carpeta, fuentes, modo)
        ]

    if modelos_detectados:
        return modelos_detectados

    hay_legacy = any(
        carpeta is not None and carpeta.exists()
        for fuente in fuentes
        for carpeta in [CARPETAS_LEGACY_ALGORITMOS.get((fuente, modo))]
    )
    if hay_legacy:
        logger.warning(
            "No se detectaron carpetas por modelo. Se usara la estructura antigua "
            "en output/ como modelo 'base'."
        )
        return [("base", output_root, True)]

    return []


def _recopilar_csvs_modelo(
    modelo: str,
    modelo_dir: Path,
    legacy: bool,
    fuentes: list,
    modo: str,
    logger: logging.Logger,
) -> List[Path]:
    csvs = []
    for fuente in fuentes:
        if legacy:
            carpeta = CARPETAS_LEGACY_ALGORITMOS.get((fuente, modo))
        else:
            carpeta = modelo_dir / CARPETAS_POR_FUENTE[fuente].format(modo=modo)
        if not carpeta.exists():
            logger.warning(f"Carpeta no encontrada [{modelo}]: {carpeta}")
            continue
        encontrados = sorted(carpeta.glob("*.csv"))
        logger.info(f"[{modelo} / {fuente.upper()} / {modo}] {carpeta.name}: {len(encontrados)} CSVs")
        csvs.extend(encontrados)
    return csvs


def procesar_modelo_recomendador(
    modelo: str,
    modelo_dir: Path,
    legacy: bool,
    args: argparse.Namespace,
    timestamp: str,
    logger: logging.Logger,
    historico_por_usuario: Dict[int, List[int]],
    contexto_global: Dict[str, Any],
    ecs_min_usuarios: int,
) -> int:
    csvs = _recopilar_csvs_modelo(modelo, modelo_dir, legacy, args.fuente, args.modo, logger)
    if not csvs:
        logger.warning(f"Sin CSVs de algoritmos XAI para evaluar en modelo {modelo}.")
        return 0

    output_eval_dir = (
        OUTPUT_EVAL_LEGACY_DIRS[args.modo]
        if legacy
        else modelo_dir / f"metricas_evaluacion_{args.modo}"
    )
    output_eval_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"\n{'=' * 70}")
    logger.info(f"EVALUANDO MODELO RECOMENDADOR: {modelo}")
    logger.info(f"CSVs a evaluar : {len(csvs)}")
    logger.info(f"Carpeta salida : {output_eval_dir}")
    logger.info(f"{'=' * 70}\n")

    acumulado_usuario: Dict[str, Dict[str, List[pd.DataFrame]]] = {}
    acumulado_alg_raw: Dict[str, List[pd.DataFrame]] = {}

    # PASO 1 - CSV a CSV: calcular metricas de usuario
    for i, csv_path in enumerate(csvs, 1):
        nombre_algoritmo = _inferir_nombre_algoritmo(csv_path)
        logger.info(f"[{modelo}] [{i}/{len(csvs)}] {csv_path.name} -> algoritmo XAI: {nombre_algoritmo}")

        if nombre_algoritmo not in acumulado_usuario:
            acumulado_usuario[nombre_algoritmo] = {e.nombre(): [] for e in ESTRATEGIAS_USUARIO}
            acumulado_alg_raw[nombre_algoritmo] = []

        try:
            df_raw = pd.read_csv(csv_path)
            df_raw = df_raw.sort_values(
                ["usuario", "hotel_recomendado", "valor_metrica"],
                ascending=[True, True, False],
            ).reset_index(drop=True)
            df_raw["modelo_recomendador"] = modelo
            acumulado_alg_raw[nombre_algoritmo].append(df_raw)

            dfs_usuario = calcular_evaluacion_usuario(
                csv_algoritmo=csv_path,
                nombre_algoritmo=nombre_algoritmo,
                historico_por_usuario=historico_por_usuario,
                contexto_global=contexto_global,
                ks=args.ks,
                estrategias=ESTRATEGIAS_USUARIO,
            )

            for nombre_metrica, df in dfs_usuario.items():
                if df.empty:
                    continue
                df = df.copy()
                df.insert(0, "modelo_recomendador", modelo)
                acumulado_usuario[nombre_algoritmo][nombre_metrica].append(df)
                estrategia = ESTRATEGIAS_POR_NOMBRE[nombre_metrica]
                for _, fila in df.iterrows():
                    logger.info(
                        f"    modelo={modelo}  usuario={int(fila['usuario'])}  "
                        f"algoritmo={fila['algoritmo']}  "
                        + estrategia.log_fila(fila, args.ks)
                    )

        except Exception as e:
            import traceback
            logger.error(f"  Error en {csv_path.name}: {e}")
            logger.error(traceback.format_exc())

    # PASO 2 - Calcular MIL (sistema) y ECS (hotel)
    logger.info(f"\n{'=' * 70}")
    logger.info(f"CALCULANDO MIL y ECS [{modelo}]...")
    logger.info(f"{'=' * 70}\n")

    mil_strategy = next((e for e in ESTRATEGIAS_SISTEMA if isinstance(e, MILStrategy)), None)
    ecs_strategy = next((e for e in ESTRATEGIAS_HOTEL if isinstance(e, ECSStrategy)), None)

    cols_mil = mil_strategy.columnas_salida(args.ks) if mil_strategy else []
    cols_ecs = ecs_strategy.columnas_salida(args.ks) if ecs_strategy else []

    acumulado_sistema: Dict[str, pd.DataFrame] = {}
    acumulado_hotel: Dict[str, pd.DataFrame] = {}

    for nombre_algoritmo, lista_raw in acumulado_alg_raw.items():
        if not lista_raw:
            continue

        df_completo = pd.concat(lista_raw, ignore_index=True)
        n_usuarios = df_completo["usuario"].nunique()
        n_h_rec = df_completo["hotel_recomendado"].nunique()

        logger.info(f"  MIL [{modelo} / {nombre_algoritmo}]: {n_usuarios} usuarios")

        if mil_strategy:
            valores_mil = mil_strategy.calcular_sistema(
                df_completo, historico_por_usuario, args.ks, contexto_global
            )
            if valores_mil is not None:
                fila_mil = {"modelo_recomendador": modelo, "algoritmo": nombre_algoritmo}
                fila_mil.update(valores_mil)
                acumulado_sistema[nombre_algoritmo] = pd.DataFrame(
                    [fila_mil], columns=["modelo_recomendador", "algoritmo"] + cols_mil
                )
                logger.info("    " + mil_strategy.log_fila(pd.Series(fila_mil), args.ks))

        if ecs_strategy:
            conteo_h_rec = df_completo.groupby("hotel_recomendado")["usuario"].nunique()
            elegibles = int((conteo_h_rec >= ecs_min_usuarios).sum())
            logger.info(
                f"  ECS [{modelo} / {nombre_algoritmo}]: {n_h_rec} hoteles, "
                f"{elegibles} con >={ecs_min_usuarios} usuario(s)"
            )

            if elegibles == 0:
                logger.warning(f"  ECS [{modelo} / {nombre_algoritmo}]: ningun hotel elegible.")
            else:
                try:
                    df_ecs = ecs_strategy.calcular_hotel(
                        df_completo, args.ks, contexto_global,
                        min_usuarios=ecs_min_usuarios,
                    )
                    if df_ecs is not None and not df_ecs.empty:
                        df_ecs["modelo_recomendador"] = modelo
                        df_ecs["algoritmo"] = nombre_algoritmo
                        cols_orden = [
                            "modelo_recomendador", "hotel_recomendado",
                            "n_usuarios", "algoritmo",
                        ] + cols_ecs
                        df_ecs = df_ecs[cols_orden]
                        acumulado_hotel[nombre_algoritmo] = df_ecs
                        logger.info(
                            f"    ECS -> {len(df_ecs)} hoteles | "
                            f"ECS_medio={round(df_ecs['ECS'].mean(), 6)}"
                        )
                except Exception as e:
                    import traceback
                    logger.error(f"    Error calculando ECS [{modelo} / {nombre_algoritmo}]: {e}")
                    logger.error(traceback.format_exc())

    # PASO 3 - Guardar CSVs
    logger.info(f"\n{'=' * 70}")
    logger.info(f"GUARDANDO CSVs [{modelo}]...")
    logger.info(f"{'=' * 70}\n")

    n_guardados = 0

    for nombre_algoritmo, metricas_dfs in sorted(acumulado_usuario.items()):
        for estrategia in ESTRATEGIAS_USUARIO:
            nombre_metrica = estrategia.nombre()
            lista_dfs = metricas_dfs.get(nombre_metrica, [])
            if not lista_dfs:
                logger.warning(f"  Sin datos: {modelo} / {nombre_algoritmo} / {nombre_metrica}")
                continue
            df_final = (
                pd.concat(lista_dfs, ignore_index=True)
                .sort_values(["modelo_recomendador", "usuario"])
                .reset_index(drop=True)
            )
            nombre_salida = f"evaluacion_{modelo}_{nombre_algoritmo}_{nombre_metrica}_{timestamp}.csv"
            df_final.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
            n_guardados += 1
            logger.info(f"  Guardado {nombre_salida} ({len(df_final)} usuarios)")

    for nombre_algoritmo, df_mil in sorted(acumulado_sistema.items()):
        nombre_salida = f"evaluacion_{modelo}_{nombre_algoritmo}_MIL_{timestamp}.csv"
        df_mil.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
        n_guardados += 1
        logger.info(f"  Guardado {nombre_salida} (1 fila)")

    for nombre_algoritmo, df_ecs in sorted(acumulado_hotel.items()):
        nombre_salida = f"evaluacion_{modelo}_{nombre_algoritmo}_ECS_{timestamp}.csv"
        df_ecs.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
        n_guardados += 1
        logger.info(f"  Guardado {nombre_salida} ({len(df_ecs)} hoteles)")

    logger.info(f"\nModelo {modelo} completado: {n_guardados} CSVs -> {output_eval_dir}")
    return n_guardados


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
    parser.add_argument(
        "--modelo", nargs="+", default=None,
        help="Modelo(s) recomendadores concretos a evaluar, por ejemplo FunkSVD ItemKNN. "
             "Si no se indica, se detectan automaticamente en output/."
    )
    parser.add_argument(
        "--ecs-min-usuarios", type=int, default=None,
        help="Mínimo de usuarios por hotel_recomendado para calcular ECS. "
             "Por defecto: 1 en modo muestra, 2 en completo/semi."
    )
    args = parser.parse_args()

    ecs_min_usuarios = args.ecs_min_usuarios if args.ecs_min_usuarios is not None \
        else (1 if args.modo == "muestra" else 2)

    logger          = setup_logging(args.modo)
    timestamp       = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("=" * 70)
    logger.info(f"PIPELINE EVALUACIÓN XAI — MODO={args.modo.upper()}  FUENTE={args.fuente}")
    logger.info(f"Histórico       : {CSV_HISTORICO}")
    logger.info(f"Cutoffs @k      : {args.ks}")
    logger.info(f"Métricas eval   : {[e.nombre() for e in ESTRATEGIAS_EVALUACION]}")
    logger.info(f"ECS min_usuarios: {ecs_min_usuarios}")
    logger.info(f"Modelos         : {args.modelo if args.modelo else 'auto'}")
    logger.info(f"Output root     : {OUTPUT_ROOT}")
    logger.info("=" * 70)

    if not CSV_HISTORICO.exists():
        logger.error(f"❌ No se encontró el CSV de histórico: {CSV_HISTORICO}")
        sys.exit(1)

    # Cargar histórico UNA sola vez
    logger.info("📖 Cargando histórico...")
    historico_por_usuario, contexto_global = cargar_historico(CSV_HISTORICO)
    modelos_detectados = _descubrir_modelos(
        OUTPUT_ROOT, args.fuente, args.modo, args.modelo, logger
    )
    if not modelos_detectados:
        logger.error("No se encontraron carpetas de modelos recomendadores para evaluar.")
        sys.exit(1)

    logger.info("Modelos a evaluar:")
    for modelo, modelo_dir, legacy in modelos_detectados:
        estructura = "legacy" if legacy else "por_modelo"
        logger.info(f"  - {modelo}: {modelo_dir} ({estructura})")

    total_guardados = 0
    for modelo, modelo_dir, legacy in modelos_detectados:
        total_guardados += procesar_modelo_recomendador(
            modelo=modelo,
            modelo_dir=modelo_dir,
            legacy=legacy,
            args=args,
            timestamp=timestamp,
            logger=logger,
            historico_por_usuario=historico_por_usuario,
            contexto_global=contexto_global,
            ecs_min_usuarios=ecs_min_usuarios,
        )

    logger.info(f"\n{'=' * 70}")
    logger.info("EVALUACION COMPLETADA")
    logger.info(f"   Modelos procesados: {len(modelos_detectados)}")
    logger.info(f"   CSVs generados    : {total_guardados}")
    logger.info(f"{'=' * 70}")
    return
    logger.info(f"   {len(historico_por_usuario)} usuarios en histórico\n")

    acumulado_usuario: Dict[str, Dict[str, List[pd.DataFrame]]] = {}
    acumulado_alg_raw: Dict[str, List[pd.DataFrame]] = {}

    # -------------------------------------------------------
    # PASO 1 — CSV a CSV: calcular métricas de usuario
    # -------------------------------------------------------
    for i, csv_path in enumerate(csvs, 1):
        nombre_algoritmo = _inferir_nombre_algoritmo(csv_path)
        logger.info(f"[{i}/{len(csvs)}] {csv_path.name}  →  algoritmo: {nombre_algoritmo}")

        if nombre_algoritmo not in acumulado_usuario:
            acumulado_usuario[nombre_algoritmo] = {e.nombre(): [] for e in ESTRATEGIAS_USUARIO}
            acumulado_alg_raw[nombre_algoritmo] = []

        try:
            df_raw = pd.read_csv(csv_path)
            df_raw = df_raw.sort_values(
                ["usuario", "hotel_recomendado", "valor_metrica"],
                ascending=[True, True, False],
            ).reset_index(drop=True)
            acumulado_alg_raw[nombre_algoritmo].append(df_raw)

            dfs_usuario = calcular_evaluacion_usuario(
                csv_algoritmo=csv_path,
                nombre_algoritmo=nombre_algoritmo,
                historico_por_usuario=historico_por_usuario,
                contexto_global=contexto_global,
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
    logger.info("CALCULANDO MIL (granularidad sistema) y ECS (granularidad hotel)...")
    logger.info(f"{'=' * 70}\n")

    mil_strategy = next((e for e in ESTRATEGIAS_SISTEMA if isinstance(e, MILStrategy)), None)
    ecs_strategy = next((e for e in ESTRATEGIAS_HOTEL  if isinstance(e, ECSStrategy)), None)

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

        logger.info(f"  MIL [{nombre_algoritmo}]: {n_usuarios} usuarios en el df acumulado")

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
                logger.info("    " + mil_strategy.log_fila(pd.Series(fila_mil), args.ks))

        # --- ECS ---
        if ecs_strategy:
            conteo_h_rec = df_completo.groupby("hotel_recomendado")["usuario"].nunique()
            elegibles = int((conteo_h_rec >= ecs_min_usuarios).sum())
            logger.info(
                f"  ECS [{nombre_algoritmo}]: {n_h_rec} hoteles distintos, "
                f"{elegibles} con ≥{ecs_min_usuarios} usuario(s) → calculando ECS..."
            )

            if elegibles == 0:
                logger.warning(
                    f"  ⚠️  ECS [{nombre_algoritmo}]: ningún hotel elegible. "
                    f"No se generará CSV de ECS."
                )
            else:
                try:
                    df_ecs = ecs_strategy.calcular_hotel(
                        df_completo, args.ks, contexto_global,
                        min_usuarios=ecs_min_usuarios,
                    )
                    if df_ecs is not None and not df_ecs.empty:
                        df_ecs["algoritmo"] = nombre_algoritmo
                        cols_orden = ["hotel_recomendado", "n_usuarios", "algoritmo"] + cols_ecs
                        df_ecs = df_ecs[cols_orden]
                        acumulado_hotel[nombre_algoritmo] = df_ecs
                        ecs_medio = df_ecs["ECS"].mean()
                        logger.info(
                            f"    ECS → {len(df_ecs)} hoteles  |  "
                            f"ECS_medio={round(ecs_medio, 6)}"
                        )
                        for _, fila in df_ecs.head(5).iterrows():
                            logger.info("      " + ecs_strategy.log_fila(fila, args.ks))
                    else:
                        logger.warning(
                            f"  ⚠️  ECS [{nombre_algoritmo}]: calcular_hotel() "
                            f"devolvió DataFrame vacío pese a {elegibles} elegibles."
                        )
                except Exception as e:
                    import traceback
                    logger.error(f"    ❌ Error calculando ECS [{nombre_algoritmo}]: {e}")
                    logger.error(traceback.format_exc())

    # -------------------------------------------------------
    # PASO 3 — Guardar CSVs
    # -------------------------------------------------------
    logger.info(f"\n{'=' * 70}")
    logger.info("GUARDANDO CSVs POR ALGORITMO Y MÉTRICA...")
    logger.info(f"{'=' * 70}\n")

    n_guardados = 0

    # AggDiv, IXD (granularidad usuario)
    for nombre_algoritmo, metricas_dfs in sorted(acumulado_usuario.items()):
        for estrategia in ESTRATEGIAS_USUARIO:
            nombre_metrica = estrategia.nombre()
            lista_dfs = metricas_dfs.get(nombre_metrica, [])
            if not lista_dfs:
                logger.warning(f"  ⚠️  Sin datos: {nombre_algoritmo} / {nombre_metrica}")
                continue
            df_final = (
                pd.concat(lista_dfs, ignore_index=True)
                .sort_values("usuario")
                .reset_index(drop=True)
            )
            nombre_salida = f"evaluacion_{nombre_algoritmo}_{nombre_metrica}_{timestamp}.csv"
            df_final.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
            n_guardados += 1
            logger.info(f"  💾 {nombre_salida}  ({len(df_final)} usuarios)")

    # MIL (granularidad sistema)
    for nombre_algoritmo, df_mil in sorted(acumulado_sistema.items()):
        nombre_salida = f"evaluacion_{nombre_algoritmo}_MIL_{timestamp}.csv"
        df_mil.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
        n_guardados += 1
        logger.info(f"  💾 {nombre_salida}  (1 fila — sistema completo)")

    # ECS (granularidad hotel)
    for nombre_algoritmo, df_ecs in sorted(acumulado_hotel.items()):
        nombre_salida = f"evaluacion_{nombre_algoritmo}_ECS_{timestamp}.csv"
        df_ecs.to_csv(output_eval_dir / nombre_salida, index=False, encoding="utf-8")
        n_guardados += 1
        logger.info(f"  💾 {nombre_salida}  ({len(df_ecs)} hoteles recomendados)")

    logger.info(f"\n{'=' * 70}")
    logger.info("✅ EVALUACIÓN COMPLETADA")
    logger.info(f"   Métricas calculadas  : {[e.nombre() for e in ESTRATEGIAS_EVALUACION]}")
    logger.info(f"   Algoritmos procesados: {len(acumulado_usuario)}")
    logger.info(f"   CSVs generados       : {n_guardados}  →  {output_eval_dir}")
    logger.info(f"{'=' * 70}")


if __name__ == "__main__":
    main()
