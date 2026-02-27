from abc import ABC, abstractmethod
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from collections import Counter
import ast
from typing import Dict, List, Any

# ============================================================
# MODE: 'muestra' o 'completo'
# ============================================================
MODE = "muestra"  # Cambiar a "completo" para procesar todos los usuarios

# ============================================================
# DEFINICIÓN DE RUTAS RELATIVAS (desde la ubicación de este script)
# ============================================================
# Este script está en: src/extraccion_metricas_conocimiento/métricas.py
SCRIPT_DIR = Path(__file__).resolve().parent  # .../extraccion_metricas_conocimiento/

# Subir niveles hasta llegar a la raíz
# ../  → src/
# ../../  → raíz del proyecto
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Definir rutas relativas desde la raíz
DATA_DIR = PROJECT_ROOT / "data"
EXPLICACIONES_HISTORICO_Y_REC = DATA_DIR / f"explicaciones_historico_y_recomendacion_{MODE}"




# ============================================================================
# ESTRATEGIA BASE (Interfaz comun)
# ============================================================================

class MetricaStrategy(ABC):
    @abstractmethod
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        pass
    
    @abstractmethod
    def nombre(self) -> str:
        pass


# ============================================================================
# METRICAS DE COBERTURA
# ============================================================================

class PropiedadesCompartidasStrategy(MetricaStrategy):
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0
        return row['num_propiedades_compartidas'].values[0]
    def nombre(self): return 'num_propiedades_compartidas'


class RatioPropiedadesCompartidasStrategy(MetricaStrategy):
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0
        num_compartidas = row['num_propiedades_compartidas'].values[0]
        row_hist = df_historicos[
            (df_historicos['usuario'] == usuario) &
            (df_historicos['hotel_historico'] == hotel_hist)
        ]
        if len(row_hist) == 0:
            return 0
        total_hist = row_hist['num_propiedades'].values[0]
        if total_hist == 0:
            return 0
        return num_compartidas / total_hist
    def nombre(self): return 'ratio_propiedades_compartidas'


class CoberturaTiposPropiedadesStrategy(MetricaStrategy):
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        tipos = {tipo for _, tipo in props}
        return len(tipos)
    def nombre(self): return 'cobertura_tipos_propiedades'


# ============================================================================
# METRICAS DE RANKING
# ============================================================================

class PrecisionAtKStrategy(MetricaStrategy):
    def __init__(self, k: int = 5):
        self.k = k
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(propiedades_explicacion) == 0:
            return 0.0
        propiedades_explicacion = propiedades_explicacion[:self.k]
        relevantes = sum(1 for p in propiedades_explicacion if p in perfil)
        return relevantes / len(propiedades_explicacion)
    def nombre(self): return f'precision_at_{self.k}'


class RecallAtKStrategy(MetricaStrategy):
    def __init__(self, k: int = 5):
        self.k = k
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(perfil) == 0:
            return 0.0
        propiedades_explicacion = propiedades_explicacion[:self.k]
        relevantes = sum(1 for p in propiedades_explicacion if p in perfil)
        return relevantes / len(perfil)
    def nombre(self): return f'recall_at_{self.k}'


class F1AtKStrategy(MetricaStrategy):
    def __init__(self, k: int = 5):
        self.k = k
        self.precision_strategy = PrecisionAtKStrategy(k)
        self.recall_strategy = RecallAtKStrategy(k)
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        precision = self.precision_strategy.calcular(df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist)
        recall = self.recall_strategy.calcular(df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist)
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    def nombre(self): return f'f1_at_{self.k}'


class NDCGStrategy(MetricaStrategy):
    def __init__(self, k: int = 5):
        self.k = k
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(propiedades_explicacion) == 0:
            return 0.0
        propiedades_explicacion = propiedades_explicacion[:self.k]
        dcg = 0.0
        for i, prop in enumerate(propiedades_explicacion, start=1):
            relevancia = perfil.get(prop, 0)
            dcg += relevancia / np.log2(i + 1)
        relevancias_ideales = sorted([perfil.get(p, 0) for p in propiedades_explicacion], reverse=True)
        idcg = sum(rel / np.log2(i + 1) for i, rel in enumerate(relevancias_ideales, start=1) if rel > 0)
        if idcg == 0:
            return 0.0
        return dcg / idcg
    def nombre(self): return f'ndcg_at_{self.k}'


class MRRStrategy(MetricaStrategy):
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(propiedades_explicacion) == 0:
            return 0.0
        for i, prop in enumerate(propiedades_explicacion, start=1):
            if prop in perfil:
                return 1.0 / i
        return 0.0
    def nombre(self): return 'mrr'


class HitRateStrategy(MetricaStrategy):
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        for prop in propiedades_explicacion:
            if prop in perfil:
                return 1.0
        return 0.0
    def nombre(self): return 'hit_rate'


class MAPStrategy(MetricaStrategy):
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(propiedades_explicacion) == 0:
            return 0.0
        suma_precision = 0.0
        num_relevantes = 0
        for k, prop in enumerate(propiedades_explicacion, start=1):
            if prop in perfil:
                num_relevantes += 1
                precision_k = num_relevantes / k
                suma_precision += precision_k
        if num_relevantes == 0:
            return 0.0
        return suma_precision / num_relevantes
    def nombre(self): return 'map'


# ============================================================================
# METRICAS DE DIVERSIDAD Y NOVEDAD
# ============================================================================

class DiversidadTiposStrategy(MetricaStrategy):
    """Shannon Entropy de los tipos semanticos en la explicacion."""
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0.0
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        tipos = [tipo for _, tipo in props]
        if len(tipos) == 0:
            return 0.0
        contador_tipos = Counter(tipos)
        total = len(tipos)
        entropy = 0.0
        for count in contador_tipos.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        return entropy
    def nombre(self): return 'diversidad_tipos_shannon'


class NovedadPropiedadesStrategy(MetricaStrategy):
    """Proporcion de propiedades poco frecuentes en el perfil (<=threshold)."""
    def __init__(self, threshold: int = 2):
        self.threshold = threshold
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(propiedades_explicacion) == 0:
            return 0.0
        novedosas = sum(1 for p in propiedades_explicacion if perfil.get(p, 0) <= self.threshold)
        return novedosas / len(propiedades_explicacion)
    def nombre(self): return f'novedad_threshold_{self.threshold}'


class SerendipiaStrategy(MetricaStrategy):
    """Propiedades que NO estan en el perfil pero aparecen en la explicacion."""
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(propiedades_explicacion) == 0:
            return 0.0
        serendipicas = sum(1 for p in propiedades_explicacion if p not in perfil)
        return serendipicas / len(propiedades_explicacion)
    def nombre(self): return 'serendipia'


# ============================================================================
# METRICAS DE CONSISTENCIA Y FIDELIDAD
# ============================================================================

class ConsistenciaTiposStrategy(MetricaStrategy):
    """Los tipos de la explicacion coinciden con los tipos frecuentes del perfil?"""
    def _obtener_perfil_tipos_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            tipos = [tipo for _, tipo in props]
            contador.update(tipos)
        return dict(contador)
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0.0
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        if len(props) == 0:
            return 0.0
        perfil_tipos = self._obtener_perfil_tipos_usuario(df_historicos, usuario)
        if len(perfil_tipos) == 0:
            return 0.0
        tipos_explicacion = [tipo for _, tipo in props]
        tipos_consistentes = sum(1 for t in tipos_explicacion if t in perfil_tipos)
        return tipos_consistentes / len(tipos_explicacion)
    def nombre(self): return 'consistencia_tipos'


class PesoPonderadoPerfilStrategy(MetricaStrategy):
    """Suma de frecuencias del perfil para las propiedades de la explicacion, normalizada."""
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        return dict(contador)
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return []
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return [p[0] if isinstance(p, tuple) else p for p in props]
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(propiedades_explicacion) == 0 or len(perfil) == 0:
            return 0.0
        suma_frecuencias = sum(perfil.get(p, 0) for p in propiedades_explicacion)
        k = len(propiedades_explicacion)
        top_k_frecuencias = sorted(perfil.values(), reverse=True)[:k]
        max_posible = sum(top_k_frecuencias)
        if max_posible == 0:
            return 0.0
        return suma_frecuencias / max_posible
    def nombre(self): return 'peso_ponderado_perfil'


class SimilaridadJaccardStrategy(MetricaStrategy):
    """Jaccard = |A interseccion B| / |A union B| entre propiedades y perfil."""
    def _obtener_perfil_usuario(self, df_historicos, usuario):
        rows = df_historicos[df_historicos['usuario'] == usuario]
        propiedades_set = set()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            propiedades_set.update(propiedades_solo)
        return propiedades_set
    def _obtener_propiedades_explicacion(self, df_comparacion, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return set()
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        return set([p[0] if isinstance(p, tuple) else p for p in props])
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(df_comparacion, usuario, hotel_rec, hotel_hist)
        if len(perfil) == 0 or len(propiedades_explicacion) == 0:
            return 0.0
        interseccion = len(perfil & propiedades_explicacion)
        union = len(perfil | propiedades_explicacion)
        if union == 0:
            return 0.0
        return interseccion / union
    def nombre(self): return 'jaccard_similarity'


# ============================================================================
# METRICAS DE BALANCE Y DISTRIBUCION
# ============================================================================

class BalanceTiposPropiedadesStrategy(MetricaStrategy):
    """1 - Gini sobre distribucion de tipos. Cercano a 1 = balanceado."""
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0.0
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        tipos = [tipo for _, tipo in props]
        if len(tipos) <= 1:
            return 1.0
        contador_tipos = Counter(tipos)
        frecuencias = sorted(contador_tipos.values())
        n = len(frecuencias)
        suma_acumulada = sum((i + 1) * freq for i, freq in enumerate(frecuencias))
        gini = (2 * suma_acumulada) / (n * sum(frecuencias)) - (n + 1) / n
        return 1 - gini
    def nombre(self): return 'balance_tipos_gini'


class RiquezaExplicativaStrategy(MetricaStrategy):
    """sqrt(num_propiedades * tipos_unicos), normalizado."""
    def calcular(self, df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist):
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0.0
        props = row['propiedades_compartidas'].values[0]
        if isinstance(props, str):
            props = ast.literal_eval(props)
        if len(props) == 0:
            return 0.0
        num_propiedades = len(props)
        tipos_unicos = len(set(tipo for _, tipo in props))
        max_riqueza = np.sqrt(10 * 5)
        riqueza = np.sqrt(num_propiedades * tipos_unicos)
        return min(riqueza / max_riqueza, 1.0)
    def nombre(self): return 'riqueza_explicativa'


# ============================================================================
# CONTEXTO - Coordinador de Metricas
# ============================================================================

class CalculadorMetricas:
    """
    Contexto que coordina el calculo de multiples metricas.
    Permite anadir/remover estrategias dinamicamente.
    """
    
    def __init__(self):
        self.estrategias: List[MetricaStrategy] = []
    
    def agregar_estrategia(self, estrategia: MetricaStrategy) -> None:
        self.estrategias.append(estrategia)
    
    def agregar_estrategias(self, estrategias: List[MetricaStrategy]) -> None:
        self.estrategias.extend(estrategias)
    
    def limpiar_estrategias(self) -> None:
        self.estrategias = []
    
    def calcular_todas(self, df_comparacion, df_historicos,
                       usuario, hotel_rec, hotel_hist) -> Dict[str, float]:
        resultados = {
            'usuario': usuario,
            'hotel_recomendado': hotel_rec,
            'hotel_historico': hotel_hist
        }
        for estrategia in self.estrategias:
            try:
                valor = estrategia.calcular(df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist)
                resultados[estrategia.nombre()] = valor
            except Exception as e:
                print(f"Error calculando {estrategia.nombre()}: {str(e)}")
                resultados[estrategia.nombre()] = None
        return resultados
    
    def calcular_para_usuario(self, usuario: int) -> List[Dict[str, Any]]:
        """
        Calcula todas las metricas para todas las combinaciones de un usuario.
        UNICO CAMBIO respecto al original: usa rutas de config en vez de rutas relativas.
        """
        archivo_comparacion = EXPLICACIONES_HISTORICO_Y_REC / f'explicaciones_usuario_{usuario}_hotel_his_y_rec.csv'
        archivo_historicos  = EXPLICACIONES_HISTORICO       / f'explicaciones_usuario_{usuario}_hotel_his.csv'

        print(f"  Buscando explicaciones en:")
        print(f"    {archivo_comparacion}")
        print(f"    {archivo_historicos}")

        df_comparacion = pd.read_csv(archivo_comparacion)
        df_historicos  = pd.read_csv(archivo_historicos)

        print(f"     Comparaciones cargadas: {len(df_comparacion)} registros")
        print(f"     Historicos cargados: {len(df_historicos)} registros")

        resultados = []

        print(f"  Calculando {len(self.estrategias)} metricas para usuario {usuario}...")
        for _, row in df_comparacion.iterrows():
            metricas = self.calcular_todas(
                df_comparacion, df_historicos,
                row['usuario'], row['hotel_recomendado'], row['hotel_historico']
            )
            resultados.append(metricas)

        return resultados