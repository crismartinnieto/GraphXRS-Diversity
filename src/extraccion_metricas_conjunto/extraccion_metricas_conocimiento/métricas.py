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
SCRIPT_DIR = Path(__file__).parent  # .../extraccion_metricas_conocimiento/

# Subir niveles hasta llegar a la raíz
# ../  → src/
# ../../  → raíz del proyecto
PROJECT_ROOT = Path(".")  # Directorio de trabajo = raíz del proyecto

# Definir rutas relativas desde la raíz
DATA_DIR = PROJECT_ROOT / "data"
EXPLICACIONES_HISTORICO_Y_REC = DATA_DIR / f"explicaciones_historico_y_recomendacion_{MODE}"
EXPLICACIONES_HISTORICO = DATA_DIR / f"explicaciones_historico_{MODE}"

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