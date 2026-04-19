"""
src/evaluacion/metricas_evaluacion.py

Módulo de EVALUACIÓN XAI — Patrón Estrategia.

MÉTRICAS IMPLEMENTADAS:
    - AggDiv   (Diversidad Agregada a nivel usuario)
    - IXD      (Inter-eXplanation Diversity)
    - MIL      (Mean Inter-List Diversity de explicadores)
    - ECS      (Explanation Consistency Score)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

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
        """'usuario', 'sistema' o 'hotel'."""
        pass

    def calcular_usuario(self, df_usuario_algoritmo, historico_usuario, ks, contexto_global=None):
        return None

    def calcular_sistema(self, df_algoritmo, historico_por_usuario, ks, contexto_global=None):
        return None

    def calcular_hotel(self, df_algoritmo, ks, contexto_global=None, min_usuarios=2):
        return None

    def columnas_salida(self, ks):
        return []

    def log_fila(self, fila, ks):
        cols = self.columnas_salida(ks)
        partes = [f"{col}={fila.get(col, 'N/A')}" for col in cols if col in fila.index]
        return "  ".join(partes)


# ============================================================
# MÉTRICA: AggDiv
# ============================================================

class AggDivStrategy(MetricaEvaluacionStrategy):

    def nombre(self):
        return "AggDiv"

    def granularidad(self):
        return "usuario"

    def columnas_salida(self, ks):
        cols = ["AggDiv", "AggDiv_norm"]
        for k in ks:
            cols += [f"AggDiv@{k}", f"AggDiv@{k}_norm"]
        return cols

    def calcular_usuario(self, df_usuario_algoritmo, historico_usuario, ks, contexto_global=None):
        n_hist = len(historico_usuario)
        union_total: Set[int] = set()
        union_k: Dict[int, Set[int]] = {k: set() for k in ks}
        for _, df_par in df_usuario_algoritmo.groupby("hotel_recomendado"):
            exp = set(int(x) for x in df_par["hotel_explicador"])
            union_total |= exp
            for k in ks:
                union_k[k] |= set(int(x) for x in df_par.head(k)["hotel_explicador"])
        aggdiv = len(union_total)
        resultado = {
            "AggDiv":      aggdiv,
            "AggDiv_norm": round(aggdiv / n_hist, 6) if n_hist > 0 else float("nan"),
        }
        for k in ks:
            aggdiv_k = len(union_k[k])
            resultado[f"AggDiv@{k}"]      = aggdiv_k
            resultado[f"AggDiv@{k}_norm"] = round(aggdiv_k / n_hist, 6) if n_hist > 0 else float("nan")
        return resultado

    def log_fila(self, fila, ks):
        partes = [f"AggDiv={fila.get('AggDiv')} (norm={fila.get('AggDiv_norm')})"]
        partes += [f"@{k}={fila.get(f'AggDiv@{k}', 'N/A')} (norm={fila.get(f'AggDiv@{k}_norm', 'N/A')})" for k in ks]
        return "  ".join(partes)


# ============================================================
# MÉTRICA: IXD
# ============================================================

class IXDStrategy(MetricaEvaluacionStrategy):

    def nombre(self):
        return "IXD"

    def granularidad(self):
        return "usuario"

    def columnas_salida(self, ks):
        return ["IXD"] + [f"IXD@{k}" for k in ks]

    def calcular_usuario(self, df_usuario_algoritmo, historico_usuario, ks, contexto_global=None):
        grupos = {
            hotel_rec: set(int(x) for x in df_par["hotel_explicador"])
            for hotel_rec, df_par in df_usuario_algoritmo.groupby("hotel_recomendado")
        }
        R = len(grupos)
        resultado = {"IXD": self._calcular_ixd(grupos, R)}
        for k in ks:
            grupos_k = {
                hotel_rec: set(int(x) for x in df_par.head(k)["hotel_explicador"])
                for hotel_rec, df_par in df_usuario_algoritmo.groupby("hotel_recomendado")
            }
            resultado[f"IXD@{k}"] = self._calcular_ixd(grupos_k, R)
        return resultado

    def log_fila(self, fila, ks):
        partes = [f"IXD={fila.get('IXD')}"]
        partes += [f"IXD@{k}={fila.get(f'IXD@{k}', 'N/A')}" for k in ks]
        return "  ".join(partes)

    @staticmethod
    def _calcular_ixd(grupos, R):
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

    def nombre(self):
        return "MIL"

    def granularidad(self):
        return "sistema"

    def columnas_salida(self, ks):
        return ["MIL"] + [f"MIL@{k}" for k in ks]

    def calcular_sistema(self, df_algoritmo, historico_por_usuario, ks, contexto_global=None):
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
                    union_por_k[k] |= set(int(x) for x in df_par.head(k)["hotel_explicador"])
            xu_completo[u] = union_total
            for k in ks:
                xu_k[k][u] = union_por_k[k]
        resultado = {"MIL": self._calcular_mil(xu_completo)}
        for k in ks:
            resultado[f"MIL@{k}"] = self._calcular_mil(xu_k[k])
        return resultado

    def log_fila(self, fila, ks):
        partes = [f"MIL={fila.get('MIL')}"]
        partes += [f"MIL@{k}={fila.get(f'MIL@{k}', 'N/A')}" for k in ks]
        return "  ".join(partes)

    @staticmethod
    def _calcular_mil(xu):
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
                total += 0.0 if union == 0 else 1.0 - (inter / union)
        return round(total / (U ** 2 - U), 6)


# ============================================================
# MÉTRICA: ECS
# ============================================================

class ECSStrategy(MetricaEvaluacionStrategy):

    def nombre(self):
        return "ECS"

    def granularidad(self):
        return "hotel"

    def columnas_salida(self, ks):
        return ["ECS"] + [f"ECS@{k}" for k in ks]

    def calcular_hotel(self, df_algoritmo, ks, contexto_global=None, min_usuarios=2):
        filas = []
        for h_rec, df_h in df_algoritmo.groupby("hotel_recomendado"):
            n_usuarios = df_h["usuario"].nunique()
            if n_usuarios < min_usuarios:
                continue
            xu_completo: Dict[int, Set[int]] = {}
            xu_k: Dict[int, Dict[int, Set[int]]] = {k: {} for k in ks}
            for usuario, df_u_h in df_h.groupby("usuario"):
                u = int(usuario)
                df_sorted = df_u_h.sort_values("valor_metrica", ascending=False)
                xu_completo[u] = set(int(x) for x in df_sorted["hotel_explicador"])
                for k in ks:
                    xu_k[k][u] = set(int(x) for x in df_sorted.head(k)["hotel_explicador"])
            fila = {
                "hotel_recomendado": int(h_rec),
                "n_usuarios":        n_usuarios,
                "ECS":               self._jaccard_medio(xu_completo),
            }
            for k in ks:
                fila[f"ECS@{k}"] = self._jaccard_medio(xu_k[k])
            filas.append(fila)

        columnas = ["hotel_recomendado", "n_usuarios"] + self.columnas_salida(ks)
        if not filas:
            return pd.DataFrame(columns=columnas)
        return (
            pd.DataFrame(filas, columns=columnas)
            .sort_values("hotel_recomendado")
            .reset_index(drop=True)
        )

    def log_fila(self, fila, ks):
        partes = [
            f"h_rec={fila.get('hotel_recomendado')}  "
            f"n_usuarios={fila.get('n_usuarios')}  "
            f"ECS={fila.get('ECS')}"
        ]
        partes += [f"ECS@{k}={fila.get(f'ECS@{k}', 'N/A')}" for k in ks]
        return "  ".join(partes)

    @staticmethod
    def _jaccard_medio(xu):
        usuarios = list(xu.keys())
        U = len(usuarios)
        if U < 2:
            return float("nan")
        total = 0.0
        n_pares = 0
        for i in range(U):
            for j in range(i + 1, U):
                u, v = usuarios[i], usuarios[j]
                inter = len(xu[u] & xu[v])
                union = len(xu[u] | xu[v])
                total += 1.0 if union == 0 else inter / union
                n_pares += 1
        return float("nan") if n_pares == 0 else round(total / n_pares, 6)


# ============================================================
# REGISTRO
# ============================================================

ESTRATEGIAS_EVALUACION: List[MetricaEvaluacionStrategy] = [
    AggDivStrategy(),
    IXDStrategy(),
    MILStrategy(),
    ECSStrategy(),
]


# ============================================================
# FUNCIONES PÚBLICAS
# ============================================================

def cargar_historico(csv_historico: str | Path) -> Tuple[Dict[int, List[int]], Dict[str, Any]]:
    """
    Carga el CSV de histórico UNA sola vez.
    Llamar una vez en el pipeline y pasar el resultado a calcular_evaluacion_usuario().

    Retorna (historico_por_usuario, contexto_global).
    """
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
    contexto_global = {
        "freq_explicador":  df_hist.groupby("hotel")["usuario"].nunique().to_dict(),
        "n_usuarios_total": df_hist["usuario"].nunique(),
    }
    return historico_por_usuario, contexto_global


def calcular_evaluacion_usuario(
    csv_algoritmo: str | Path,
    nombre_algoritmo: str,
    historico_por_usuario: Dict[int, List[int]],
    contexto_global: Dict[str, Any],
    ks: List[int] = None,
    estrategias: List[MetricaEvaluacionStrategy] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Calcula métricas de granularidad 'usuario' para un CSV de algoritmo.

    IMPORTANTE: pasar historico_por_usuario y contexto_global ya cargados
    (via cargar_historico()) para no releer el histórico en cada llamada.

    Devuelve {nombre_metrica: DataFrame} con UNA fila por usuario.
    MIL y ECS NO se calculan aquí.
    """
    if ks is None:
        ks = [1, 3, 5]
    if estrategias is None:
        estrategias = [e for e in ESTRATEGIAS_EVALUACION if e.granularidad() == "usuario"]

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
        filas = []
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