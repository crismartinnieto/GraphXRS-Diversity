"""
Módulo para calcular métricas de cobertura en explicaciones XAI
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter


class CoverageMetrics:
    """
    Clase para calcular métricas de cobertura de explicaciones
    basadas en propiedades compartidas entre hoteles
    """
    
    def __init__(self, df_explicaciones: pd.DataFrame):
        """
        Args:
            df_explicaciones: DataFrame con propiedades compartidas
                Columnas esperadas: user, hotel_recomendado, hotel_ejemplo_id,
                                   numero_propiedades, lista_propiedades
        """
        self.df_explicaciones = df_explicaciones.copy()
        self.resultados: List[Dict] = []
        
        # Validar columnas necesarias
        required_cols = {'user', 'hotel_recomendado', 'hotel_ejemplo_id', 
                        'numero_propiedades', 'lista_propiedades'}
        if not required_cols.issubset(set(df_explicaciones.columns)):
            raise ValueError(f"El DataFrame debe contener las columnas: {required_cols}")
    
    def _extraer_propiedades_completas(self, lista_propiedades_str: str) -> List[str]:
        """
        Extrae las propiedades COMPLETAS (la parte después de ':')
        
        Ejemplos:
            'category:Tours' -> 'Tours'
            'city:Philadelphia' -> 'Philadelphia'
            'attribute:RestaurantsPriceRange2=2' -> 'RestaurantsPriceRange2=2'
        
        Args:
            lista_propiedades_str: String con propiedades separadas por ' | '
            
        Returns:
            Lista de propiedades completas (valores después de ':')
        """
        if pd.isna(lista_propiedades_str) or lista_propiedades_str == '':
            return []
        
        propiedades_completas = []
        props_list = str(lista_propiedades_str).split(' | ')
        
        for prop in props_list:
            prop = prop.strip()
            if ':' in prop:
                # Tomar solo la parte después de ':'
                valor = prop.split(':', 1)[1].strip()
                if valor:
                    propiedades_completas.append(valor)
            elif prop:  # Por si hay propiedades sin ':'
                propiedades_completas.append(prop)
        
        return propiedades_completas
    
    def calcular_cobertura_usuario(self, user_id: int) -> Dict:
        """
        Calcula métricas agregadas para un usuario específico
        (para mantener compatibilidad con análisis globales)
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con métricas agregadas del usuario
        """
        user_data = self.df_explicaciones[
            self.df_explicaciones['user'] == user_id
        ].copy()
        
        if len(user_data) == 0:
            return {
                'user': user_id,
                'num_recomendaciones': 0,
                'num_ejemplos_totales': 0,
                'promedio_propiedades': 0.0,
                'max_propiedades': 0,
                'min_propiedades': 0,
                'std_propiedades': 0.0,
                'cobertura_ejemplos': 0.0,
                'diversidad_propiedades': 0.0,
                'tasa_sin_propiedades': 0.0
            }
        
        hoteles_recomendados = user_data['hotel_recomendado'].unique()
        num_propiedades = user_data['numero_propiedades']
        
        metrics = {
            'user': user_id,
            'num_recomendaciones': len(hoteles_recomendados),
            'num_ejemplos_totales': len(user_data),
            'promedio_propiedades': float(num_propiedades.mean()),
            'max_propiedades': int(num_propiedades.max()),
            'min_propiedades': int(num_propiedades.min()),
            'std_propiedades': float(num_propiedades.std()) if len(num_propiedades) > 1 else 0.0,
            'cobertura_ejemplos': float(self._calcular_cobertura_ejemplos(user_data)),
            'diversidad_propiedades': float(self._calcular_diversidad_propiedades(user_data)),
            'tasa_sin_propiedades': float(self._calcular_tasa_sin_propiedades(user_data))
        }
        
        return metrics
    
    def _calcular_cobertura_ejemplos(self, user_data: pd.DataFrame) -> float:
        """
        Calcula la cobertura promedio de ejemplos por recomendación
        """
        ejemplos_por_recomendacion = user_data.groupby('hotel_recomendado').size()
        return ejemplos_por_recomendacion.mean()
    
    def _calcular_diversidad_propiedades(self, user_data: pd.DataFrame) -> float:
        """
        Calcula la diversidad de propiedades (valores completos después de ':')
        """
        todas_propiedades = []
        for props in user_data['lista_propiedades'].dropna():
            propiedades_completas = self._extraer_propiedades_completas(props)
            todas_propiedades.extend(propiedades_completas)
        
        if len(todas_propiedades) == 0:
            return 0.0
        
        propiedades_unicas = len(set(todas_propiedades))
        total_propiedades = len(todas_propiedades)
        
        return propiedades_unicas / total_propiedades
    
    def _calcular_tasa_sin_propiedades(self, user_data: pd.DataFrame) -> float:
        """
        Calcula el porcentaje de explicaciones sin propiedades compartidas
        """
        sin_propiedades = (user_data['numero_propiedades'] == 0).sum()
        total = len(user_data)
        return sin_propiedades / total if total > 0 else 0.0
    
    def calcular_cobertura_global(self) -> Dict:
        """
        Calcula métricas de cobertura a nivel global (todos los usuarios)
        """
        usuarios = self.df_explicaciones['user'].unique()
        pares_unicos = self.df_explicaciones.groupby(
            ['user', 'hotel_recomendado']
        ).size().shape[0]
        
        num_props = self.df_explicaciones['numero_propiedades']
        
        metrics = {
            'usuarios_con_explicacion': int(len(usuarios)),
            'pares_usuario_hotel': int(pares_unicos),
            'total_explicaciones': len(self.df_explicaciones),
            'promedio_propiedades_global': float(num_props.mean()),
            'mediana_propiedades_global': float(num_props.median()),
            'std_propiedades_global': float(num_props.std()),
            'max_propiedades_global': int(num_props.max()),
            'min_propiedades_global': int(num_props.min()),
            'promedio_ejemplos_por_recomendacion': float(self._calcular_ejemplos_promedio()),
            'tasa_global_sin_propiedades': float((num_props == 0).sum() / len(num_props)),
        }
        
        # Análisis de propiedades COMPLETAS (valores después de ':')
        cobertura_props = self._calcular_cobertura_propiedades_global()
        metrics.update(cobertura_props)
        
        return metrics
    
    def _calcular_ejemplos_promedio(self) -> float:
        """
        Calcula el promedio de ejemplos por cada par (usuario, hotel_recomendado)
        """
        ejemplos_por_par = self.df_explicaciones.groupby(
            ['user', 'hotel_recomendado']
        ).size()
        return ejemplos_por_par.mean()
    
    def _calcular_cobertura_propiedades_global(self) -> Dict:
        """
        Analiza qué VALORES de propiedades se usan más (después de ':')
        
        Ejemplo: De 'city:Philadelphia' extrae 'Philadelphia'
        """
        todas_propiedades = []
        
        for props in self.df_explicaciones['lista_propiedades'].dropna():
            propiedades_completas = self._extraer_propiedades_completas(props)
            todas_propiedades.extend(propiedades_completas)
        
        if len(todas_propiedades) == 0:
            return {
                'total_propiedades_usadas': 0,
                'propiedades_unicas': 0,
                'num_valores_distintos': 0,
                'top_10_valores': '{}'
            }
        
        conteo_propiedades = Counter(todas_propiedades)
        top_10 = dict(conteo_propiedades.most_common(10))
        
        return {
            'total_propiedades_usadas': len(todas_propiedades),
            'propiedades_unicas': len(set(todas_propiedades)),
            'num_valores_distintos': len(conteo_propiedades),
            'top_10_valores': str(top_10)
        }
    
    def generar_reporte_detallado(self) -> pd.DataFrame:
        """
        Genera un reporte JERÁRQUICO con 3 niveles:
        
        NIVEL 1: Explicaciones individuales (user, hotel_recomendado, hotel_historico)
        NIVEL 2: Resumen por hotel recomendado (user, hotel_recomendado, NaN)
        NIVEL 3: Resumen global por usuario (user, NaN, NaN)
        
        Returns:
            DataFrame ordenado jerárquicamente
        """
        print("Generando reporte detallado jerárquico...")
        
        nivel1_filas = []  # Explicaciones individuales
        nivel2_filas = []  # Resúmenes por hotel
        nivel3_filas = []  # Resúmenes por usuario
        
        usuarios = self.df_explicaciones['user'].unique()
        
        for user_id in usuarios:
            # Calcular métricas agregadas del usuario (NIVEL 3)
            user_metrics = self.calcular_cobertura_usuario(user_id)
            
            user_data = self.df_explicaciones[
                self.df_explicaciones['user'] == user_id
            ]
            
            hoteles_recomendados = user_data['hotel_recomendado'].unique()
            
            # Procesar cada hotel recomendado
            for hotel_rec in hoteles_recomendados:
                hotel_data = user_data[
                    user_data['hotel_recomendado'] == hotel_rec
                ]
                
                # Calcular métricas del par (usuario, hotel_recomendado) - NIVEL 2
                num_ejemplos_hotel = len(hotel_data)
                promedio_props_hotel = float(hotel_data['numero_propiedades'].mean())
                max_props_hotel = int(hotel_data['numero_propiedades'].max())
                min_props_hotel = int(hotel_data['numero_propiedades'].min())
                std_props_hotel = float(hotel_data['numero_propiedades'].std()) if len(hotel_data) > 1 else 0.0
                
                # NIVEL 1: Añadir cada explicación individual
                for _, row in hotel_data.iterrows():
                    nivel1_filas.append({
                        'user': user_id,
                        'hotel_recomendado': hotel_rec,
                        'hotel_historico': row['hotel_ejemplo_id'],
                        
                        # Métricas de la explicación individual
                        'numero_propiedades': int(row['numero_propiedades']),
                        'lista_propiedades': row['lista_propiedades'],
                        
                        # Métricas del hotel recomendado (NIVEL 2) - vacías en NIVEL 1
                        'num_ejemplos_hotel': None,
                        'promedio_props_hotel': None,
                        'max_props_hotel': None,
                        'min_props_hotel': None,
                        'std_props_hotel': None,
                        
                        # Métricas globales del usuario (NIVEL 3) - vacías en NIVEL 1
                        'num_recomendaciones_usuario': None,
                        'num_ejemplos_totales_usuario': None,
                        'promedio_props_usuario': None,
                        'max_props_usuario': None,
                        'min_props_usuario': None,
                        'std_props_usuario': None,
                        'cobertura_ejemplos_usuario': None,
                        'diversidad_usuario': None,
                        'tasa_sin_propiedades_usuario': None
                    })
                
                # NIVEL 2: Añadir fila RESUMEN del hotel recomendado
                nivel2_filas.append({
                    'user': user_id,
                    'hotel_recomendado': hotel_rec,
                    'hotel_historico': None,
                    
                    # Métricas individuales - vacías en NIVEL 2
                    'numero_propiedades': None,
                    'lista_propiedades': None,
                    
                    # Métricas del hotel recomendado (NIVEL 2)
                    'num_ejemplos_hotel': num_ejemplos_hotel,
                    'promedio_props_hotel': promedio_props_hotel,
                    'max_props_hotel': max_props_hotel,
                    'min_props_hotel': min_props_hotel,
                    'std_props_hotel': std_props_hotel,
                    
                    # Métricas globales del usuario (NIVEL 3) - vacías en NIVEL 2
                    'num_recomendaciones_usuario': None,
                    'num_ejemplos_totales_usuario': None,
                    'promedio_props_usuario': None,
                    'max_props_usuario': None,
                    'min_props_usuario': None,
                    'std_props_usuario': None,
                    'cobertura_ejemplos_usuario': None,
                    'diversidad_usuario': None,
                    'tasa_sin_propiedades_usuario': None
                })
            
            # NIVEL 3: Añadir fila RESUMEN GLOBAL del usuario
            nivel3_filas.append({
                'user': user_id,
                'hotel_recomendado': None,
                'hotel_historico': None,
                
                # Métricas individuales - vacías en NIVEL 3
                'numero_propiedades': None,
                'lista_propiedades': None,
                
                # Métricas del hotel recomendado (NIVEL 2) - vacías en NIVEL 3
                'num_ejemplos_hotel': None,
                'promedio_props_hotel': None,
                'max_props_hotel': None,
                'min_props_hotel': None,
                'std_props_hotel': None,
                
                # Métricas globales del usuario (NIVEL 3)
                'num_recomendaciones_usuario': user_metrics['num_recomendaciones'],
                'num_ejemplos_totales_usuario': user_metrics['num_ejemplos_totales'],
                'promedio_props_usuario': user_metrics['promedio_propiedades'],
                'max_props_usuario': user_metrics['max_propiedades'],
                'min_props_usuario': user_metrics['min_propiedades'],
                'std_props_usuario': user_metrics['std_propiedades'],
                'cobertura_ejemplos_usuario': user_metrics['cobertura_ejemplos'],
                'diversidad_usuario': user_metrics['diversidad_propiedades'],
                'tasa_sin_propiedades_usuario': user_metrics['tasa_sin_propiedades']
            })
        
        # Concatenar en orden jerárquico: NIVEL 1 -> NIVEL 2 -> NIVEL 3
        df_resultados = pd.concat([
            pd.DataFrame(nivel1_filas),
            pd.DataFrame(nivel2_filas),
            pd.DataFrame(nivel3_filas)
        ], ignore_index=True)
        
        # Reordenar columnas para mejor legibilidad
        columnas_orden = [
            # Identificadores
            'user', 'hotel_recomendado', 'hotel_historico',
            # NIVEL 1: Métricas individuales
            'numero_propiedades', 'lista_propiedades',
            # NIVEL 2: Métricas por hotel recomendado
            'num_ejemplos_hotel', 'promedio_props_hotel', 'max_props_hotel', 
            'min_props_hotel', 'std_props_hotel',
            # NIVEL 3: Métricas globales del usuario
            'num_recomendaciones_usuario', 'num_ejemplos_totales_usuario',
            'promedio_props_usuario', 'max_props_usuario', 'min_props_usuario',
            'std_props_usuario', 'cobertura_ejemplos_usuario', 'diversidad_usuario',
            'tasa_sin_propiedades_usuario'
        ]
        
        df_resultados = df_resultados[columnas_orden]
        
        print(f"\n✓ Reporte jerárquico generado:")
        print(f"  - Total de filas: {len(df_resultados)}")
        print(f"  - NIVEL 1 (explicaciones individuales): {len(nivel1_filas)}")
        print(f"  - NIVEL 2 (resúmenes por hotel): {len(nivel2_filas)}")
        print(f"  - NIVEL 3 (resúmenes por usuario): {len(nivel3_filas)}")
        
        # Mostrar métricas globales del sistema
        print("\n" + "="*70)
        print("MÉTRICAS GLOBALES DEL SISTEMA")
        print("="*70)
        
        global_metrics = self.calcular_cobertura_global()
        for key, value in global_metrics.items():
            if isinstance(value, float):
                print(f"{key:.<50} {value:.4f}")
            else:
                print(f"{key:.<50} {value}")
        
        print("="*70)
        
        return df_resultados
    
    def guardar_resultados(self, output_path: str):
        """
        Genera y guarda el reporte jerárquico en CSV
        
        Args:
            output_path: Ruta donde guardar el CSV de resultados
        """
        df_resultados = self.generar_reporte_detallado()
        
        df_resultados.to_csv(output_path, index=False)
        print(f"\n✓ Resultados guardados en: {output_path}")
        print(f"  Total de filas: {len(df_resultados)}")
        