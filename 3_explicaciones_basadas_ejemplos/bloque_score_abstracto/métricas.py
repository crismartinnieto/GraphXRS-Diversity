from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
import ast
from typing import Dict, List, Any


# ============================================================================
# ESTRATEGIA BASE (Interfaz común)
# ============================================================================

class MetricaStrategy(ABC):
    """
    Interfaz Strategy que define el contrato para todas las métricas.
    Cada métrica concreta implementa su propia lógica de cálculo.
    """
    
    @abstractmethod
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        """
        Calcula la métrica específica.
        
        Args:
            df_comparacion: DataFrame con comparaciones hotel_rec vs hotel_hist
            df_historicos: DataFrame con hoteles históricos del usuario
            usuario: ID del usuario
            hotel_rec: ID del hotel recomendado
            hotel_hist: ID del hotel histórico
            
        Returns:
            Valor de la métrica calculada
        """
        pass
    
    @abstractmethod
    def nombre(self) -> str:
        """Retorna el nombre de la métrica para identificación"""
        pass


# ============================================================================
# ESTRATEGIAS CONCRETAS - MÉTRICAS DE COBERTURA
# ============================================================================

class PropiedadesCompartidasStrategy(MetricaStrategy):
    """Número de propiedades compartidas entre hotel histórico y recomendado"""
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0
        return row['num_propiedades_compartidas'].values[0]
    
    def nombre(self) -> str:
        return 'num_propiedades_compartidas'


class RatioPropiedadesCompartidasStrategy(MetricaStrategy):
    """Ratio de propiedades compartidas sobre total del hotel histórico"""
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        # Obtener propiedades compartidas
        row = df_comparacion[
            (df_comparacion['usuario'] == usuario) &
            (df_comparacion['hotel_recomendado'] == hotel_rec) &
            (df_comparacion['hotel_historico'] == hotel_hist)
        ]
        if len(row) == 0:
            return 0
        num_compartidas = row['num_propiedades_compartidas'].values[0]
        
        # Obtener total de propiedades del histórico
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
    
    def nombre(self) -> str:
        return 'ratio_propiedades_compartidas'


class CoberturaTiposPropiedadesStrategy(MetricaStrategy):
    """Número de tipos únicos de propiedades compartidas"""
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
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
    
    def nombre(self) -> str:
        return 'cobertura_tipos_propiedades'


# ============================================================================
# ESTRATEGIAS CONCRETAS - MÉTRICAS DE RANKING
# ============================================================================

class PrecisionAtKStrategy(MetricaStrategy):
    """Precision@k: Proporción de propiedades compartidas que son relevantes"""
    
    def __init__(self, k: int = 5):
        self.k = k
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        """Obtiene el perfil del usuario con frecuencias de propiedades"""
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
        """Obtiene las propiedades compartidas de una explicación específica"""
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(propiedades_explicacion) == 0:
            return 0.0
        
        propiedades_explicacion = propiedades_explicacion[:self.k]
        relevantes = sum(1 for p in propiedades_explicacion if p in perfil)
        
        return relevantes / len(propiedades_explicacion)
    
    def nombre(self) -> str:
        return f'precision_at_{self.k}'


class RecallAtKStrategy(MetricaStrategy):
    """Recall@k: Proporción del perfil del usuario cubierta por las top-k propiedades"""
    
    def __init__(self, k: int = 5):
        self.k = k
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(perfil) == 0:
            return 0.0
        
        propiedades_explicacion = propiedades_explicacion[:self.k]
        relevantes = sum(1 for p in propiedades_explicacion if p in perfil)
        
        return relevantes / len(perfil)
    
    def nombre(self) -> str:
        return f'recall_at_{self.k}'


class F1AtKStrategy(MetricaStrategy):
    """F1@k: Media armónica entre Precision@k y Recall@k"""
    
    def __init__(self, k: int = 5):
        self.k = k
        self.precision_strategy = PrecisionAtKStrategy(k)
        self.recall_strategy = RecallAtKStrategy(k)
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        precision = self.precision_strategy.calcular(
            df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist
        )
        recall = self.recall_strategy.calcular(
            df_comparacion, df_historicos, usuario, hotel_rec, hotel_hist
        )
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def nombre(self) -> str:
        return f'f1_at_{self.k}'


class NDCGStrategy(MetricaStrategy):
    """NDCG: Normalized Discounted Cumulative Gain"""
    
    def __init__(self, k: int = 5):
        self.k = k
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(propiedades_explicacion) == 0:
            return 0.0
        
        propiedades_explicacion = propiedades_explicacion[:self.k]
        
        # Calcular DCG
        dcg = 0.0
        for i, prop in enumerate(propiedades_explicacion, start=1):
            relevancia = perfil.get(prop, 0)
            dcg += relevancia / np.log2(i + 1)
        
        # Calcular IDCG
        relevancias_ideales = sorted([perfil.get(p, 0) for p in propiedades_explicacion], reverse=True)
        idcg = sum(rel / np.log2(i + 1) for i, rel in enumerate(relevancias_ideales, start=1) if rel > 0)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    def nombre(self) -> str:
        return f'ndcg_at_{self.k}'


class MRRStrategy(MetricaStrategy):
    """MRR: Mean Reciprocal Rank"""
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(propiedades_explicacion) == 0:
            return 0.0
        
        for i, prop in enumerate(propiedades_explicacion, start=1):
            if prop in perfil:
                return 1.0 / i
        
        return 0.0
    
    def nombre(self) -> str:
        return 'mrr'


class HitRateStrategy(MetricaStrategy):
    """Hit Rate: ¿Hay al menos UNA propiedad relevante?"""
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        for prop in propiedades_explicacion:
            if prop in perfil:
                return 1.0
        
        return 0.0
    
    def nombre(self) -> str:
        return 'hit_rate'


class MAPStrategy(MetricaStrategy):
    """MAP: Mean Average Precision"""
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
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
    
    def nombre(self) -> str:
        return 'map'


# ============================================================================
# MÉTRICAS ADICIONALES - DIVERSIDAD Y NOVEDAD
# ============================================================================

class DiversidadTiposStrategy(MetricaStrategy):
    """
    Diversidad de tipos semánticos en la explicación.
    Mide qué tan variada es la explicación en términos de tipos de propiedades.
    Shannon Entropy de los tipos semánticos.
    """
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
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
        
        # Contar frecuencia de cada tipo
        tipos = [tipo for _, tipo in props]
        if len(tipos) == 0:
            return 0.0
        
        contador_tipos = Counter(tipos)
        total = len(tipos)
        
        # Shannon Entropy
        entropy = 0.0
        for count in contador_tipos.values():
            p = count / total
            if p > 0:
                entropy -= p * np.log2(p)
        
        return entropy
    
    def nombre(self) -> str:
        return 'diversidad_tipos_shannon'


class NovedadPropiedadesStrategy(MetricaStrategy):
    """
    Novedad: Proporción de propiedades compartidas que son POCO frecuentes en el perfil.
    Una propiedad es novedosa si aparece <= threshold veces en el historial.
    """
    
    def __init__(self, threshold: int = 2):
        self.threshold = threshold
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(propiedades_explicacion) == 0:
            return 0.0
        
        # Contar propiedades novedosas (poco frecuentes)
        novedosas = sum(1 for p in propiedades_explicacion 
                       if perfil.get(p, 0) <= self.threshold)
        
        return novedosas / len(propiedades_explicacion)
    
    def nombre(self) -> str:
        return f'novedad_threshold_{self.threshold}'


class SerendipiaStrategy(MetricaStrategy):
    """
    Serendipia: Propiedades que NO están en el perfil pero son relevantes.
    Captura propiedades "sorprendentes pero buenas" en la explicación.
    """
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(propiedades_explicacion) == 0:
            return 0.0
        
        # Contar propiedades NO vistas antes (serendipity)
        serendipicas = sum(1 for p in propiedades_explicacion if p not in perfil)
        
        return serendipicas / len(propiedades_explicacion)
    
    def nombre(self) -> str:
        return 'serendipia'


# ============================================================================
# MÉTRICAS DE CONSISTENCIA Y FIDELIDAD
# ============================================================================

class ConsistenciaTiposStrategy(MetricaStrategy):
    """
    Consistencia de tipos: ¿Los tipos de propiedades en la explicación 
    coinciden con los tipos más frecuentes del perfil del usuario?
    """
    
    def _obtener_perfil_tipos_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        """Obtiene frecuencia de TIPOS semánticos en el perfil"""
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            tipos = [tipo for _, tipo in props]
            contador.update(tipos)
        
        return dict(contador)
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
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
        
        # Obtener tipos del perfil
        perfil_tipos = self._obtener_perfil_tipos_usuario(df_historicos, usuario)
        
        if len(perfil_tipos) == 0:
            return 0.0
        
        # Contar tipos en explicación que están en el perfil
        tipos_explicacion = [tipo for _, tipo in props]
        tipos_consistentes = sum(1 for t in tipos_explicacion if t in perfil_tipos)
        
        return tipos_consistentes / len(tipos_explicacion)
    
    def nombre(self) -> str:
        return 'consistencia_tipos'


class PesoPonderadoPerfilStrategy(MetricaStrategy):
    """
    Peso ponderado: Suma de las frecuencias (del perfil) de las propiedades 
    en la explicación, normalizada por el máximo posible.
    Prioriza explicaciones con propiedades MUY frecuentes en el historial.
    """
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> Dict:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        contador = Counter()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            contador.update(propiedades_solo)
        
        return dict(contador)
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> List:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(propiedades_explicacion) == 0 or len(perfil) == 0:
            return 0.0
        
        # Suma de frecuencias de las propiedades en la explicación
        suma_frecuencias = sum(perfil.get(p, 0) for p in propiedades_explicacion)
        
        # Máximo posible: las K propiedades más frecuentes del perfil
        k = len(propiedades_explicacion)
        top_k_frecuencias = sorted(perfil.values(), reverse=True)[:k]
        max_posible = sum(top_k_frecuencias)
        
        if max_posible == 0:
            return 0.0
        
        return suma_frecuencias / max_posible
    
    def nombre(self) -> str:
        return 'peso_ponderado_perfil'


class SimilaridadJaccardStrategy(MetricaStrategy):
    """
    Similitud Jaccard entre propiedades compartidas y perfil del usuario.
    Jaccard = |A ∩ B| / |A ∪ B|
    """
    
    def _obtener_perfil_usuario(self, df_historicos: pd.DataFrame, usuario: int) -> set:
        rows = df_historicos[df_historicos['usuario'] == usuario]
        
        propiedades_set = set()
        for props in rows['propiedades'].values:
            if isinstance(props, str):
                props = ast.literal_eval(props)
            propiedades_solo = [p[0] if isinstance(p, tuple) else p for p in props]
            propiedades_set.update(propiedades_solo)
        
        return propiedades_set
    
    def _obtener_propiedades_explicacion(self, df_comparacion: pd.DataFrame,
                                        usuario: int, hotel_rec: int, hotel_hist: int) -> set:
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
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
        perfil = self._obtener_perfil_usuario(df_historicos, usuario)
        propiedades_explicacion = self._obtener_propiedades_explicacion(
            df_comparacion, usuario, hotel_rec, hotel_hist
        )
        
        if len(perfil) == 0 or len(propiedades_explicacion) == 0:
            return 0.0
        
        interseccion = len(perfil & propiedades_explicacion)
        union = len(perfil | propiedades_explicacion)
        
        if union == 0:
            return 0.0
        
        return interseccion / union
    
    def nombre(self) -> str:
        return 'jaccard_similarity'


# ============================================================================
# MÉTRICAS DE BALANCE Y DISTRIBUCIÓN
# ============================================================================

class BalanceTiposPropiedadesStrategy(MetricaStrategy):
    """
    Balance de tipos: Mide qué tan equilibrada es la distribución de tipos.
    Gini coefficient invertido (1 - Gini) para medir igualdad.
    Valor cercano a 1 = muy balanceado, cercano a 0 = desbalanceado
    """
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
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
            return 1.0  # Perfectamente balanceado (trivial)
        
        contador_tipos = Counter(tipos)
        frecuencias = sorted(contador_tipos.values())
        
        # Gini coefficient
        n = len(frecuencias)
        suma_acumulada = sum((i + 1) * freq for i, freq in enumerate(frecuencias))
        gini = (2 * suma_acumulada) / (n * sum(frecuencias)) - (n + 1) / n
        
        # Retornar balance (inverso de Gini)
        return 1 - gini
    
    def nombre(self) -> str:
        return 'balance_tipos_gini'


class RiquezaExplicativaStrategy(MetricaStrategy):
    """
    Riqueza explicativa: Combina número de propiedades con diversidad de tipos.
    Penaliza explicaciones muy largas pero poco diversas.
    """
    
    def calcular(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                 usuario: int, hotel_rec: int, hotel_hist: int) -> float:
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
        
        # Riqueza = sqrt(num_propiedades * tipos_únicos)
        # Normalizado por un máximo razonable (ej: 10 props, 5 tipos)
        max_riqueza = np.sqrt(10 * 5)
        riqueza = np.sqrt(num_propiedades * tipos_unicos)
        
        return min(riqueza / max_riqueza, 1.0)
    
    def nombre(self) -> str:
        return 'riqueza_explicativa'


# ============================================================================
# CONTEXTO - Coordinador de Métricas
# ============================================================================

class CalculadorMetricas:
    """
    Contexto que coordina el cálculo de múltiples métricas.
    Permite añadir/remover estrategias dinámicamente.
    """
    
    def __init__(self):
        self.estrategias: List[MetricaStrategy] = []
    
    def agregar_estrategia(self, estrategia: MetricaStrategy) -> None:
        """Agrega una nueva estrategia de métrica"""
        self.estrategias.append(estrategia)
    
    def agregar_estrategias(self, estrategias: List[MetricaStrategy]) -> None:
        """Agrega múltiples estrategias de métricas"""
        self.estrategias.extend(estrategias)
    
    def limpiar_estrategias(self) -> None:
        """Limpia todas las estrategias"""
        self.estrategias = []
    
    def calcular_todas(self, df_comparacion: pd.DataFrame, df_historicos: pd.DataFrame,
                      usuario: int, hotel_rec: int, hotel_hist: int) -> Dict[str, float]:
        """
        Calcula todas las métricas registradas para una combinación específica.
        
        Returns:
            Diccionario con nombre_metrica: valor
        """
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
        Calcula todas las métricas para todas las combinaciones de un usuario.
        
        Returns:
            Lista de diccionarios con todas las métricas calculadas
        """
        
        # Obtener directorio del archivo actual
        script_dir = Path(__file__).resolve().parent
        
        # Subir un nivel y entrar en explicaciones_basadas_ejemplos/data/
        explicaciones_dir = script_dir.parent / 'explicaciones_basadas_ejemplos' / 'data'
        
        print(f"  📂 Buscando explicaciones en: {explicaciones_dir}")
        
        # Verificar que existan los archivos
        archivo_comparacion = explicaciones_dir / f'explicaciones_usuario_{usuario}_hotel_his_y_rec.csv'
        archivo_historicos = explicaciones_dir / f'explicaciones_usuario_{usuario}_hotel_his.csv'
    

        # Cargar datos del usuario
        df_comparacion = pd.read_csv(archivo_comparacion)
        df_historicos = pd.read_csv(archivo_historicos)
        
        print(f"     ✓ Comparaciones cargadas: {len(df_comparacion)} registros")
        print(f"     ✓ Históricos cargados: {len(df_historicos)} registros")
        
        resultados = []
        
        print(f"  Calculando {len(self.estrategias)} métricas para usuario {usuario}...")
        for _, row in df_comparacion.iterrows():
            metricas = self.calcular_todas(
                df_comparacion, df_historicos,
                row['usuario'], row['hotel_recomendado'], row['hotel_historico']
            )
            resultados.append(metricas)
        
        return resultados

