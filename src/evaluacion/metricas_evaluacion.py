"""
src/evaluacion/metricas_evaluacion.py

Módulo de EVALUACIÓN XAI — Patrón Estrategia.

MÉTRICAS IMPLEMENTADAS:
    - AggDiv   (Diversidad Agregada a nivel usuario)
               AggDiv'   = |⋃_{r∈R} X_r|
               AggDiv'@k = |⋃_{r∈R} X_r@k|
               Granularidad: usuario + algoritmo
               Columnas salida: usuario | historico_num | algoritmo |
                                AggDiv | AggDiv@1 | AggDiv@3 | AggDiv@5

    - IXD      (Inter-eXplanation Diversity)
               Granularidad: usuario + algoritmo
               Columnas salida: usuario | historico_num | algoritmo |
                                IXD | IXD@1 | IXD@3 | IXD@5

    - MIL      (Mean Inter-List Diversity de explicadores)
               MIL = 1 - (1/|U|²) · Σ_u Σ_v |X_u ∩ X_v| / |X_u ∪ X_v|
               Granularidad: sistema (valor único por algoritmo)
               Columnas salida: algoritmo | MIL | MIL@1 | MIL@3 | MIL@5
               IMPORTANTE: debe calcularse con calcular_sistema() una vez
               acumulados TODOS los usuarios, no CSV a CSV.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd


# ============================================================
# ESTRATEGIA BASE
# ============================================================

class MetricaEvaluacionStrategy(ABC):

    @abstractmethod
    def nombre(self) -> str:
        pass

    @abstractmethod
    def granularidad(self) -> str:
        """'usuario' o 'sistema'."""
        pass

    def calcular_usuario(
        self,
        df_usuario_algoritmo: pd.DataFrame,
        historico_usuario: List[int],
        ks: List[int],
        contexto_global: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        return None

    def calcular_sistema(
        self,
        df_algoritmo: pd.DataFrame,
        historico_por_usuario: Dict[int, List[int]],
        ks: List[int],
        contexto_global: Dict[str, Any] = None,
    ) -> Optional[Dict[str, Any]]:
        return None

    def columnas_salida(self, ks: List[int]) -> List[str]:
        return []

    def log_fila(self, fila: pd.Series, ks: List[int]) -> str:
        cols = self.columnas_salida(ks)
        partes = [f"{col}={fila.get(col, 'N/A')}" for col in cols if col in fila.index]
        return "  ".join(partes)


# ============================================================
# MÉTRICA: AggDiv
# ============================================================

class AggDivStrategy(MetricaEvaluacionStrategy):

    def nombre(self) -> str:
        return "AggDiv"

    def granularidad(self) -> str:
        return "usuario"

    def columnas_salida(self, ks: List[int]) -> List[str]:
        cols = ["AggDiv", "AggDiv_norm"]
        for k in ks:
            cols += [f"AggDiv@{k}", f"AggDiv@{k}_norm"]
        return cols

    def calcular_usuario(
        self,
        df_usuario_algoritmo: pd.DataFrame,
        historico_usuario: List[int],
        ks: List[int],
        contexto_global: Dict[str, Any] = None,
    ) -> Dict[str, Any]:

        n_hist = len(historico_usuario)

        union_total: Set[int] = set()
        union_k: Dict[int, Set[int]] = {k: set() for k in ks}

        for _, df_par in df_usuario_algoritmo.groupby("hotel_recomendado"):
            exp = set(int(x) for x in df_par["hotel_explicador"])
            union_total |= exp
            for k in ks:
                top_k = set(int(x) for x in df_par.head(k)["hotel_explicador"])
                union_k[k] |= top_k

        aggdiv = len(union_total)
        resultado: Dict[str, Any] = {
            "AggDiv":      aggdiv,
            "AggDiv_norm": round(aggdiv / n_hist, 6) if n_hist > 0 else float("nan"),
        }
        for k in ks:
            aggdiv_k = len(union_k[k])
            resultado[f"AggDiv@{k}"]      = aggdiv_k
            resultado[f"AggDiv@{k}_norm"] = round(aggdiv_k / n_hist, 6) if n_hist > 0 else float("nan")

        return resultado

    def log_fila(self, fila: pd.Series, ks: List[int]) -> str:
        partes = [f"AggDiv={fila.get('AggDiv')} (norm={fila.get('AggDiv_norm')})"]
        partes += [
            f"@{k}={fila.get(f'AggDiv@{k}', 'N/A')} (norm={fila.get(f'AggDiv@{k}_norm', 'N/A')})"
            for k in ks
        ]
        return "  ".join(partes)


# ============================================================
# MÉTRICA: IXD
# ============================================================

class IXDStrategy(MetricaEvaluacionStrategy):
    """
    IXD — Diversidad Inter-Explicación (nivel usuario).

    X   = ⋃_{s∈R} X_s
    IXD = (1/|X|) · Σ_{x∈X}  |{s∈R | x∉X_s}| / (|R|−1)

    Rango [0,1]. NaN si el usuario tiene una sola recomendación.
    Una fila por usuario. Sin hotel_recomendado.
    """

    def nombre(self) -> str:
        return "IXD"

    def granularidad(self) -> str:
        return "usuario"

    def columnas_salida(self, ks: List[int]) -> List[str]:
        return ["IXD"] + [f"IXD@{k}" for k in ks]

    def calcular_usuario(
        self,
        df_usuario_algoritmo: pd.DataFrame,
        historico_usuario: List[int],
        ks: List[int],
        contexto_global: Dict[str, Any] = None,
    ) -> Dict[str, Any]:

        grupos: Dict[Any, Set[int]] = {
            hotel_rec: set(int(x) for x in df_par["hotel_explicador"])
            for hotel_rec, df_par in df_usuario_algoritmo.groupby("hotel_recomendado")
        }
        R = len(grupos)

        resultado: Dict[str, Any] = {"IXD": self._calcular_ixd(grupos, R)}

        for k in ks:
            grupos_k: Dict[Any, Set[int]] = {
                hotel_rec: set(int(x) for x in df_par.head(k)["hotel_explicador"])
                for hotel_rec, df_par in df_usuario_algoritmo.groupby("hotel_recomendado")
            }
            resultado[f"IXD@{k}"] = self._calcular_ixd(grupos_k, R)

        return resultado

    def log_fila(self, fila: pd.Series, ks: List[int]) -> str:
        partes = [f"IXD={fila.get('IXD')}"]
        partes += [f"IXD@{k}={fila.get(f'IXD@{k}', 'N/A')}" for k in ks]
        return "  ".join(partes)

    @staticmethod
    def _calcular_ixd(grupos: Dict[Any, Set[int]], R: int) -> float:
        if R <= 1:
            return float("nan")
        X_global = set().union(*grupos.values())
        if not X_global:
            return 0.0
        total = 0.0
        for x in X_global:
            n_sin_x = sum(1 for xs in grupos.values() if x not in xs)
            total += n_sin_x / (R - 1)
        return round(total / len(X_global), 6)


# ============================================================
# MÉTRICA: MIL
# ============================================================

class MILStrategy(MetricaEvaluacionStrategy):
    """
    MIL-Expl — Mean Inter-List Diversity de explicadores (nivel sistema).

    
    Rango [0,1]. NaN si hay menos de 2 usuarios.
    Una sola fila por algoritmo (toda la población).

    IMPORTANTE: llamar a calcular_sistema() con el DataFrame completo de
    TODOS los usuarios ya acumulados, no CSV a CSV.
    """

    def nombre(self) -> str:
        return "MIL"

    def granularidad(self) -> str:
        return "sistema"

    def columnas_salida(self, ks: List[int]) -> List[str]:
        return ["MIL"] + [f"MIL@{k}" for k in ks]

    def calcular_sistema(
        self,
        df_algoritmo: pd.DataFrame,
        historico_por_usuario: Dict[int, List[int]],
        ks: List[int],
        contexto_global: Dict[str, Any] = None,
    ) -> Dict[str, Any]:

        # Construir X_u para cada usuario
        xu_completo: Dict[int, Set[int]] = {}
        xu_k: Dict[int, Dict[int, Set[int]]] = {k: {} for k in ks}

        for usuario, df_u in df_algoritmo.groupby("usuario"):
            u = int(usuario)
            union_total: Set[int] = set()
            union_por_k: Dict[int, Set[int]] = {k: set() for k in ks}

            for _, df_par in df_u.groupby("hotel_recomendado"):
                exp = set(int(x) for x in df_par["hotel_explicador"])
                union_total |= exp
                for k in ks:
                    top_k = set(int(x) for x in df_par.head(k)["hotel_explicador"])
                    union_por_k[k] |= top_k

            xu_completo[u] = union_total
            for k in ks:
                xu_k[k][u] = union_por_k[k]

        resultado: Dict[str, Any] = {"MIL": self._calcular_mil(xu_completo)}
        for k in ks:
            resultado[f"MIL@{k}"] = self._calcular_mil(xu_k[k])
        return resultado

    def log_fila(self, fila: pd.Series, ks: List[int]) -> str:
        partes = [f"MIL={fila.get('MIL')}"]
        partes += [f"MIL@{k}={fila.get(f'MIL@{k}', 'N/A')}" for k in ks]
        return "  ".join(partes)

    @staticmethod
    def _calcular_mil(xu: Dict[int, Set[int]]) -> float:
        """
        MIL = 1/(|U|²-|U|) · Σ_{ua≠ub} [ 1 - q(ua,ub)/|X_ua ∪ X_ub| ]
            = 1/(|U|²-|U|) · Σ_{ua≠ub}  distancia_jaccard(X_ua, X_ub)

        q   : |X_ua ∩ X_ub|  (explicadores comunes)
        c   : |X_ua ∪ X_ub|  (unión — variable por par, no fija)
        """
        usuarios = list(xu.keys())
        U = len(usuarios)
        if U < 2:
            return float("nan")

        total = 0.0
        for u in usuarios:
            for v in usuarios:
                if u == v:
                    continue
                inter = len(xu[u] & xu[v])
                union = len(xu[u] | xu[v])
                if union == 0:
                    total += 0.0
                else:
                    total += 1.0 - (inter / union)   # distancia Jaccard

        return round(total / (U ** 2 - U), 6)


# ============================================================
# REGISTRO
# ============================================================

ESTRATEGIAS_EVALUACION: List[MetricaEvaluacionStrategy] = [
    AggDivStrategy(),
    IXDStrategy(),
    MILStrategy(),
]


# ============================================================
# FUNCIÓN PÚBLICA — solo para métricas de granularidad 'usuario'
# MIL se calcula aparte en el pipeline con el df acumulado completo
# ============================================================

def calcular_evaluacion_usuario(
    csv_historico: str | Path,
    csv_algoritmo: str | Path,
    nombre_algoritmo: str,
    ks: List[int] = None,
    estrategias: List[MetricaEvaluacionStrategy] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Calcula métricas de granularidad 'usuario' para un CSV de algoritmo.

    Devuelve un dict por métrica. Cada DataFrame tiene UNA fila por usuario:
        usuario | historico_num | algoritmo | AggDiv | AggDiv@1 | ...

    MIL NO se calcula aquí (necesita todos los usuarios acumulados).
    """
    if ks is None:
        ks = [1, 3, 5]
    if estrategias is None:
        estrategias = [e for e in ESTRATEGIAS_EVALUACION if e.granularidad() == "usuario"]

    # Cargar histórico
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

    freq_explicador = df_hist.groupby("hotel")["usuario"].nunique().to_dict()
    contexto_global = {
        "freq_explicador":  freq_explicador,
        "n_usuarios_total": df_hist["usuario"].nunique(),
    }

    # Cargar CSV del algoritmo
    df_alg = pd.read_csv(csv_algoritmo)
    df_alg = df_alg.sort_values(
        ["usuario", "hotel_recomendado", "valor_metrica"],
        ascending=[True, True, False],
    ).reset_index(drop=True)

    resultados: Dict[str, pd.DataFrame] = {}

    for estrategia in estrategias:
        if estrategia.granularidad() != "usuario":
            continue

        cols_metrica = estrategia.columnas_salida(ks)
        filas: List[Dict[str, Any]] = []

        for usuario, df_u in df_alg.groupby("usuario"):
            u = int(usuario)
            historico = historico_por_usuario.get(u, [])
            valores = estrategia.calcular_usuario(df_u, historico, ks, contexto_global)
            if valores is None:
                continue
            fila: Dict[str, Any] = {
                "usuario":       u,
                "historico_num": len(historico),
                "algoritmo":     nombre_algoritmo,
            }
            fila.update({col: valores.get(col, float("nan")) for col in cols_metrica})
            filas.append(fila)

        columnas_df = ["usuario", "historico_num", "algoritmo"] + cols_metrica
        resultados[estrategia.nombre()] = pd.DataFrame(filas, columns=columnas_df)

    return resultados