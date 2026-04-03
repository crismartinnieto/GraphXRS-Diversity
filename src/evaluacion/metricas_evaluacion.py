"""
src/evaluacion/metricas_evaluacion.py

Módulo de EVALUACIÓN XAI — Patrón Estrategia.

Calcula métricas de evaluación sobre los rankings de explicación generados
por los módulos KG y CF, cruzándolos con el histórico real del usuario.

TERMINOLOGÍA:
    - algoritmo   : el método de ranking usado para generar las explicaciones
                    (ej: "kg_num_propiedades_compartidas", "cf_betweenness_hotel")
    - metrica     : la función de evaluación aplicada sobre ese ranking
                    (ej: AggDiv, IXD, AggDiv@k)

ESTRUCTURA DEL CSV DE SALIDA (una fila por usuario, hotel_recomendado y algoritmo):
    usuario | hotel_recomendado | algoritmo |
    AggDiv | AggDiv_norm | AggDiv@1 | AggDiv@1_norm | ... |
    IXD | IXD@1 | IXD@3 | IXD@5 |
    historico_lista | historico_num

MÉTRICAS IMPLEMENTADAS:
    - AggDiv  (Diversidad Agregada de Explicaciones / Cobertura)
              → Granularidad: par (usuario, hotel_recomendado)
    - IXD     (Inter-eXplanation Diversity)
              → Granularidad: usuario (agrega sobre todas sus recomendaciones)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ============================================================
# ESTRATEGIA BASE
# ============================================================

class MetricaEvaluacionStrategy(ABC):
    """
    Interfaz base para métricas de evaluación XAI.

    Dos niveles de cálculo posibles (las subclases implementan los que apliquen):
      - calcular_par()     : por par (usuario, hotel_recomendado)  → AggDiv
      - calcular_usuario() : por usuario, agregando todos sus pares → IXD
    """

    @abstractmethod
    def nombre(self) -> str:
        """Nombre de la métrica (ej: 'AggDiv'). Usado como prefijo en columnas."""
        pass

    @abstractmethod
    def calcular_par(
        self,
        df_par: pd.DataFrame,
        historico_usuario: List[int],
        ks: List[int],
    ) -> Dict[str, Any]:
        """
        Calcula la métrica para un par (usuario, hotel_recomendado) concreto.

        Args:
            df_par           : DataFrame filtrado para ese par.
                               Columnas: [usuario, hotel_recomendado,
                                          hotel_explicador, valor_metrica]
                               Ordenado DESC por valor_metrica.
            historico_usuario: lista de business_id consumidos por el usuario.
            ks               : lista de cutoffs @k (ej: [1, 3, 5]).

        Returns:
            Dict con las claves de la métrica o NaN si no aplica a este nivel.
        """
        pass

    def calcular_usuario(
        self,
        df_usuario_algoritmo: pd.DataFrame,
        ks: List[int],
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula la métrica a nivel de usuario (agrega sobre todos sus pares).

        Args:
            df_usuario_algoritmo : DataFrame con TODAS las filas del usuario
                                   para UN algoritmo concreto.
                                   Columnas: [usuario, hotel_recomendado,
                                              hotel_explicador, valor_metrica]
                                   Ordenado DESC por valor_metrica dentro de cada par.
            ks                   : lista de cutoffs @k.

        Returns:
            Dict con las claves de la métrica, o None si no aplica a este nivel.
            El pipeline rellena con estos valores TODAS las filas del usuario
            para ese algoritmo (columna de valor único por usuario/algoritmo).
        """
        return None  # Por defecto: no aplica a nivel usuario


# ============================================================
# MÉTRICA: AggDiv  (Diversidad Agregada de Explicaciones / Cobertura)
# ============================================================

class AggDivStrategy(MetricaEvaluacionStrategy):
    """
    AggDiv — Diversidad Agregada de Explicaciones (cobertura del histórico).

    Calculado a nivel de par (usuario, hotel_recomendado).

    Fórmula:
        AggDiv        = |X_r|             (explicadores únicos para esa recomendación)
        AggDiv@k      = |X_r@k|           (los k primeros explicadores)
        AggDiv_norm   = AggDiv   / |H_u|
        AggDiv@k_norm = AggDiv@k / |H_u|

    Donde:
        X_r   = ranking de ítems explicadores para la recomendación r,
                ordenado DESC por valor del algoritmo.
        X_r@k = los k primeros explicadores de X_r.
        H_u   = histórico real del usuario (todos los hoteles consumidos).
        |H_u| = número de hoteles en el histórico.

    Interpretación:
        Mide cuántos explicadores únicos se usan para justificar CADA
        recomendación concreta. _norm divide entre |H_u| para comparar
        entre usuarios con históricos de distinto tamaño.
        Valor 1.0 → se ha usado TODO el histórico para explicar esa recomendación.
    """

    def nombre(self) -> str:
        return "AggDiv"

    def calcular_par(
        self,
        df_par: pd.DataFrame,
        historico_usuario: List[int],
        ks: List[int],
    ) -> Dict[str, Any]:

        n_historico = len(historico_usuario)
        resultado: Dict[str, Any] = {}

        # AggDiv total: todos los explicadores de esta recomendación
        todos_explicadores = set(int(x) for x in df_par["hotel_explicador"].unique())
        aggdiv_total = len(todos_explicadores)
        resultado["AggDiv"]      = aggdiv_total
        resultado["AggDiv_norm"] = (
            round(aggdiv_total / n_historico, 6) if n_historico > 0 else 0.0
        )

        # AggDiv@k: top-k explicadores (df_par ya viene ordenado desc)
        for k in ks:
            top_k     = set(int(x) for x in df_par.head(k)["hotel_explicador"].tolist())
            aggdiv_k  = len(top_k)
            resultado[f"AggDiv@{k}"]      = aggdiv_k
            resultado[f"AggDiv@{k}_norm"] = (
                round(aggdiv_k / n_historico, 6) if n_historico > 0 else 0.0
            )

        # Info del histórico
        resultado["historico_lista"] = sorted(historico_usuario)
        resultado["historico_num"]   = n_historico

        return resultado


# ============================================================
# MÉTRICA: IXD  (Inter-eXplanation Diversity)
# ============================================================

class IXDStrategy(MetricaEvaluacionStrategy):
    """
    IXD — Diversidad Inter-Explicación.

    Mide cuán diferentes son las listas de explicación entre las distintas
    recomendaciones de un mismo usuario y un mismo algoritmo.

    Fórmula (nivel usuario):
        X     = ⋃_{s∈R} X_s          (conjunto global de explicadores del usuario)
        IXD   = (1/|X|) · Σ_{x∈X}  |{s∈R | x∉X_s}| / (|R|−1)

    Rango: [0, 1]
        0.0 → todas las recomendaciones comparten exactamente los mismos
              explicadores (ninguna diversidad entre listas).
        1.0 → cada recomendación usa explicadores completamente distintos
              al resto.
        NaN → el usuario solo tiene una recomendación (IXD no está definida).

    IXD@k:
        Ídem pero restringiendo cada X_s a los top-k explicadores de esa
        recomendación antes de calcular la diversidad.

    Granularidad:
        IXD se calcula a nivel de USUARIO+ALGORITMO (un único valor por
        combinación). El pipeline lo replica en todas las filas del usuario
        para ese algoritmo, de modo que el CSV siga teniendo una fila por par.

    calcular_par() devuelve NaN para mantener compatibilidad con el bucle
    principal; el valor real se inyecta en el segundo pase del pipeline.
    """

    def nombre(self) -> str:
        return "IXD"

    # ------------------------------------------------------------------
    # Nivel par: no aplica → NaN (el pipeline lo sobreescribirá después)
    # ------------------------------------------------------------------
    def calcular_par(
        self,
        df_par: pd.DataFrame,
        historico_usuario: List[int],
        ks: List[int],
    ) -> Dict[str, Any]:
        resultado: Dict[str, Any] = {"IXD": float("nan")}
        for k in ks:
            resultado[f"IXD@{k}"] = float("nan")
        return resultado

    # ------------------------------------------------------------------
    # Nivel usuario: cálculo real
    # ------------------------------------------------------------------
    def calcular_usuario(
        self,
        df_usuario_algoritmo: pd.DataFrame,
        ks: List[int],
    ) -> Dict[str, Any]:
        """
        Calcula IXD para un usuario completo (un algoritmo concreto).

        Args:
            df_usuario_algoritmo : DataFrame filtrado a (usuario, algoritmo).
                                   Columnas: [usuario, hotel_recomendado,
                                              hotel_explicador, valor_metrica]
                                   Ordenado DESC por valor_metrica dentro de cada par.
            ks                   : cutoffs @k.

        Returns:
            Dict con claves IXD, IXD@1, IXD@3, IXD@5, ...
        """
        resultado: Dict[str, Any] = {}

        # Agrupar explicadores (set) por recomendación
        grupos: Dict[Any, set] = {
            hotel_rec: set(int(x) for x in df_par["hotel_explicador"])
            for hotel_rec, df_par in df_usuario_algoritmo.groupby("hotel_recomendado")
        }
        R = len(grupos)

        resultado["IXD"] = self._calcular_ixd(grupos, R)

        for k in ks:
            # Top-k explicadores por recomendación
            grupos_k: Dict[Any, set] = {}
            for hotel_rec, df_par in df_usuario_algoritmo.groupby("hotel_recomendado"):
                top_k = set(
                    int(x) for x in df_par.head(k)["hotel_explicador"]
                )
                grupos_k[hotel_rec] = top_k
            resultado[f"IXD@{k}"] = self._calcular_ixd(grupos_k, R)

        return resultado

    # ------------------------------------------------------------------
    # Núcleo matemático
    # ------------------------------------------------------------------
    @staticmethod
    def _calcular_ixd(grupos: Dict[Any, set], R: int) -> float:
        """
        Calcula IXD dado {hotel_rec → set_explicadores} y |R|.

        IXD = (1/|X|) · Σ_{x∈X}  |{s∈R | x∉X_s}| / (R−1)
        """
        if R <= 1:
            return float("nan")   # No definida con una sola recomendación

        X_global = set().union(*grupos.values())   # ⋃ X_s
        if not X_global:
            return 0.0

        total = 0.0
        for x in X_global:
            n_sin_x = sum(1 for xs in grupos.values() if x not in xs)
            total  += n_sin_x / (R - 1)

        return round(total / len(X_global), 6)


# ============================================================
# REGISTRO DE ESTRATEGIAS DISPONIBLES
# ============================================================

ESTRATEGIAS_EVALUACION: List[MetricaEvaluacionStrategy] = [
    AggDivStrategy(),
    IXDStrategy(),
    # Próximas métricas: IntraListDiversity, Coverage, ...
]


# ============================================================
# FUNCIÓN PÚBLICA PRINCIPAL
# ============================================================

def calcular_evaluacion(
    csv_historico: str | Path,
    csv_algoritmo: str | Path,
    nombre_algoritmo: str,
    ks: List[int] = None,
    estrategias: List[MetricaEvaluacionStrategy] = None,
) -> pd.DataFrame:
    """
    Calcula todas las métricas de evaluación para un CSV de algoritmo.

    Primer pase  → métricas por par (AggDiv, y NaN para IXD).
    Segundo pase → métricas por usuario (IXD real), replicadas en cada fila.

    Args:
        csv_historico    : ruta al CSV de interacciones reales.
                           Columnas: [user_id, business_id, rating]
        csv_algoritmo    : ruta al CSV de un algoritmo de explicación.
                           Columnas: [usuario, hotel_recomendado,
                                      hotel_explicador, valor_metrica]
        nombre_algoritmo : nombre del algoritmo fuente.
        ks               : cutoffs @k. Por defecto [1, 3, 5].
        estrategias      : estrategias a aplicar.
                           Por defecto todas las de ESTRATEGIAS_EVALUACION.

    Returns:
        DataFrame con UNA fila por par (usuario, hotel_recomendado):
            usuario | hotel_recomendado | algoritmo |
            AggDiv | AggDiv_norm | AggDiv@1 | AggDiv@1_norm | ... |
            IXD | IXD@1 | IXD@3 | IXD@5 |
            historico_lista | historico_num
    """
    if ks is None:
        ks = [1, 3, 5]
    if estrategias is None:
        estrategias = ESTRATEGIAS_EVALUACION

    # ----------------------------------------------------------
    # 1. Cargar histórico → dict { usuario_id: [hotel_id, ...] }
    # ----------------------------------------------------------
    df_hist = pd.read_csv(csv_historico)
    df_hist.columns = [c.strip().lower() for c in df_hist.columns]

    if "user_id" in df_hist.columns and "business_id" in df_hist.columns:
        df_hist = df_hist.rename(columns={"user_id": "usuario", "business_id": "hotel"})
    elif "usuario" not in df_hist.columns or "hotel" not in df_hist.columns:
        raise ValueError(
            "El CSV de histórico debe tener columnas 'user_id'/'business_id' "
            "o 'usuario'/'hotel'."
        )

    historico_por_usuario: Dict[int, List[int]] = (
        df_hist.groupby("usuario")["hotel"]
        .apply(lambda s: sorted(s.astype(int).tolist()))
        .to_dict()
    )

    # ----------------------------------------------------------
    # 2. Cargar CSV del algoritmo y ordenar desc dentro de cada par
    # ----------------------------------------------------------
    df_alg = pd.read_csv(csv_algoritmo)
    df_alg = df_alg.sort_values(
        ["usuario", "hotel_recomendado", "valor_metrica"],
        ascending=[True, True, False],
    ).reset_index(drop=True)

    # ----------------------------------------------------------
    # 3. PRIMER PASE: métricas por par (usuario, hotel_recomendado)
    #    AggDiv → valor real  |  IXD → NaN (se rellena en el segundo pase)
    # ----------------------------------------------------------
    filas_resultado = []

    for (usuario, hotel_rec), df_par in df_alg.groupby(["usuario", "hotel_recomendado"]):
        historico = historico_por_usuario.get(int(usuario), [])

        fila: Dict[str, Any] = {
            "usuario":           usuario,
            "hotel_recomendado": hotel_rec,
            "algoritmo":         nombre_algoritmo,
        }

        for estrategia in estrategias:
            valores = estrategia.calcular_par(df_par, historico, ks)
            fila.update(valores)

        filas_resultado.append(fila)

    df_out = pd.DataFrame(filas_resultado)

    # ----------------------------------------------------------
    # 4. SEGUNDO PASE: métricas por usuario (IXD)
    #    Para cada estrategia que implemente calcular_usuario(),
    #    calculamos el valor y lo replicamos en todas las filas del usuario.
    # ----------------------------------------------------------
    for estrategia in estrategias:
        for usuario, df_u in df_alg.groupby("usuario"):
            valores_usuario = estrategia.calcular_usuario(df_u, ks)
            if valores_usuario is None:
                continue  # Esta estrategia no opera a nivel usuario

            mascara = df_out["usuario"] == usuario
            for col, val in valores_usuario.items():
                df_out.loc[mascara, col] = val

    # ----------------------------------------------------------
    # 5. Ordenar columnas
    # ----------------------------------------------------------
    columnas_base = ["usuario", "hotel_recomendado", "algoritmo"]
    columnas_aggdiv = (
        ["AggDiv", "AggDiv_norm"]
        + [col for k in ks for col in (f"AggDiv@{k}", f"AggDiv@{k}_norm")]
    )
    columnas_ixd = ["IXD"] + [f"IXD@{k}" for k in ks]
    columnas_hist = ["historico_lista", "historico_num"]

    columnas_orden = [
        c for c in (columnas_base + columnas_aggdiv + columnas_ixd + columnas_hist)
        if c in df_out.columns
    ]
    df_out = df_out[columnas_orden]

    return df_out