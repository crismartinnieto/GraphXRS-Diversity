"""
Pipeline principal para calcular métricas de cobertura en XAI
"""
from pathlib import Path
import pandas as pd
from typing import Optional

from .data_loader import DataLoader
from .metrics.coverage_metrics import CoverageMetrics


class XAICoveragePipeline:
    """
    Orquestador principal del pipeline de métricas de cobertura.
    
    Este pipeline coordina:
    1. Carga de datos (recomendaciones y explicaciones)
    2. Cálculo de métricas de cobertura
    3. Generación y almacenamiento de resultados
    """
    
    def __init__(self, 
                 recomendaciones_path: str,
                 explicaciones_path: str,
                 output_path: str):
        """
        Args:
            recomendaciones_path: Ruta al CSV de recomendaciones (user, hotel_recomendado)
            explicaciones_path: Ruta al CSV de propiedades compartidas
            output_path: Ruta donde guardar los resultados
        """
        self.recomendaciones_path = Path(recomendaciones_path)
        self.explicaciones_path = Path(explicaciones_path)
        self.output_path = Path(output_path)
        
        self.data_loader: Optional[DataLoader] = None
        self.coverage_metrics: Optional[CoverageMetrics] = None
        self.df_resultados: Optional[pd.DataFrame] = None
    
    def ejecutar(self) -> pd.DataFrame:
        """
        Ejecuta el pipeline completo de principio a fin
        
        Returns:
            DataFrame con los resultados de las métricas
        """
        print("="*70)
        print(" PIPELINE XAI - MÉTRICAS DE COBERTURA DE EXPLICACIONES")
        print("="*70)
        
        # Paso 1: Cargar datos
        print("\n[PASO 1/3] Cargando datos de entrada...")
        print("-"*70)
        self._cargar_datos()
        
        # Paso 2: Calcular métricas
        print("\n[PASO 2/3] Calculando métricas de cobertura...")
        print("-"*70)
        self._calcular_metricas()
        
        # Paso 3: Guardar resultados
        print("\n[PASO 3/3] Guardando resultados...")
        print("-"*70)
        self._guardar_resultados()
        
        
        return self.df_resultados
    
    def _cargar_datos(self):
        """
        Carga y valida los datos de entrada
        """
        self.data_loader = DataLoader(
            recomendaciones_path=str(self.recomendaciones_path),
            explicaciones_path=str(self.explicaciones_path)
        )
        
        df_recomendaciones, df_explicaciones = self.data_loader.load_data()
        
        print(f"\n  Recomendaciones: {len(df_recomendaciones)} filas")
        print(f"  Usuarios únicos: {df_recomendaciones['user'].nunique()}")
        print(f"  Hoteles únicos recomendados: {df_recomendaciones['hotel_recomendado'].nunique()}")
        
        print(f"\n  Explicaciones: {len(df_explicaciones)} filas")
        print(f"  Pares (usuario, hotel): {df_explicaciones.groupby(['user', 'hotel_recomendado']).ngroups}")
    
    def _calcular_metricas(self):
        """
        Calcula todas las métricas de cobertura
        """
        _, df_explicaciones = self.data_loader.load_data()
        
        self.coverage_metrics = CoverageMetrics(df_explicaciones)
        # Ahora genera reporte DETALLADO (no agregado)
        self.df_resultados = self.coverage_metrics.generar_reporte_detallado()
        
        # Mostrar resumen estadístico solo de filas con datos (no resúmenes)
        print("\n  RESUMEN ESTADÍSTICO DE EXPLICACIONES INDIVIDUALES")
        print("  " + "-"*66)
        
        df_individuales = self.df_resultados[self.df_resultados['hotel_historico'].notna()]
        
        if len(df_individuales) > 0:
            print(f"  Promedio propiedades compartidas: {df_individuales['numero_propiedades'].mean():.2f}")
            print(f"  Máximo propiedades compartidas: {df_individuales['numero_propiedades'].max()}")
            print(f"  Mínimo propiedades compartidas: {df_individuales['numero_propiedades'].min()}")
            print(f"  Desviación estándar: {df_individuales['numero_propiedades'].std():.2f}")
    
    def _guardar_resultados(self):
        """
        Guarda los resultados en CSV
        """
        # Crear directorio si no existe
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar usando el método de CoverageMetrics
        self.coverage_metrics.guardar_resultados(str(self.output_path))
        
        print(f"\n  Archivo generado: {self.output_path.name}")
        print(f"  Ubicación: {self.output_path.parent}")
        print(f"  Tamaño: {self.output_path.stat().st_size / 1024:.2f} KB")
    
    def analizar_usuario_especifico(self, user_id: int):
        """
        Realiza un análisis detallado de un usuario específico
        
        Args:
            user_id: ID del usuario a analizar
        """
        if self.data_loader is None:
            raise RuntimeError("Debes ejecutar el pipeline primero con .ejecutar()")
        
        print(f"\n{'='*70}")
        print(f" ANÁLISIS DETALLADO - Usuario {user_id}")
        print(f"{'='*70}")
        
        # Obtener recomendaciones del usuario
        recs = self.data_loader.get_user_recommendations(user_id)
        
        if len(recs) == 0:
            print(f"\n✗ No se encontraron recomendaciones para el usuario {user_id}")
            return
        
        print(f"\n[1] RECOMENDACIONES GENERADAS")
        print("-"*70)
        print(f"  Total de hoteles recomendados: {len(recs)}")
        print(f"  Hoteles: {recs['hotel_recomendado'].tolist()}")
        
        # Obtener explicaciones para cada hotel
        print(f"\n[2] EXPLICACIONES POR HOTEL RECOMENDADO")
        print("-"*70)
        
        for idx, hotel_id in enumerate(recs['hotel_recomendado'].unique(), 1):
            expls = self.data_loader.get_user_explanations(user_id, hotel_id)
            
            print(f"\n  [{idx}] Hotel Recomendado: {hotel_id}")
            print(f"      Ejemplos usados: {len(expls)}")
            
            if len(expls) > 0:
                print(f"      Propiedades promedio: {expls['numero_propiedades'].mean():.2f}")
                print(f"      Propiedades max: {expls['numero_propiedades'].max()}")
                
                # Mostrar top 3 mejores explicaciones
                top_expls = expls.nlargest(3, 'numero_propiedades')
                
                print("\n      Top 3 Explicaciones:")
                for i, (_, row) in enumerate(top_expls.iterrows(), 1):
                    print(f"        {i}. Hotel ejemplo: {row['hotel_ejemplo_id']}")
                    print(f"           Propiedades: {row['numero_propiedades']}")
                    props_display = str(row['lista_propiedades'])[:80] + "..."
                    print(f"           {props_display}")
        
        # Métricas del usuario
        print(f"\n[3] MÉTRICAS DE COBERTURA")
        print("-"*70)
        
        metrics = self.coverage_metrics.calcular_cobertura_usuario(user_id)
        
        for key, value in metrics.items():
            if key != 'user':
                if isinstance(value, float):
                    print(f"  {key:.<50} {value:.4f}")
                else:
                    print(f"  {key:.<50} {value}")
        
        print("\n" + "="*70)
    
    def comparar_usuarios(self, user_ids: list):
        """
        Compara métricas entre varios usuarios
        
        Args:
            user_ids: Lista de IDs de usuarios a comparar
        """
        if self.df_resultados is None:
            raise RuntimeError("Debes ejecutar el pipeline primero con .ejecutar()")
        
        print(f"\n{'='*70}")
        print(f" COMPARACIÓN DE USUARIOS")
        print(f"{'='*70}")
        
        df_comp = self.df_resultados[self.df_resultados['user'].isin(user_ids)]
        
        if len(df_comp) == 0:
            print("\n✗ No se encontraron datos para los usuarios especificados")
            return
        
        print(f"\nUsuarios analizados: {user_ids}")
        print("\nMétricas comparativas:\n")
        
        # Seleccionar columnas clave
        cols_display = [
            'user', 
            'num_recomendaciones',
            'promedio_propiedades',
            'cobertura_ejemplos',
            'diversidad_propiedades'
        ]
        
        print(df_comp[cols_display].to_string(index=False))
        print("\n" + "="*70)
    
    def generar_resumen_ejecutivo(self) -> dict:
        """
        Genera un resumen ejecutivo del análisis
        
        Returns:
            Diccionario con métricas clave del sistema
        """
        if self.df_resultados is None or self.coverage_metrics is None:
            raise RuntimeError("Debes ejecutar el pipeline primero con .ejecutar()")
        
        global_metrics = self.coverage_metrics.calcular_cobertura_global()
        
        resumen = {
            'total_usuarios': len(self.df_resultados),
            'total_recomendaciones': global_metrics['pares_usuario_hotel'],
            'total_explicaciones': global_metrics['total_explicaciones'],
            'cobertura_promedio': global_metrics['promedio_propiedades_global'],
            'calidad_explicaciones': 'Alta' if global_metrics['promedio_propiedades_global'] >= 2 else 'Media'
        }
        
        print("\n" + "="*70)
        print(" RESUMEN EJECUTIVO")
        print("="*70)
        
        for key, value in resumen.items():
            print(f"  {key.replace('_', ' ').title():.<50} {value}")
        
        print("="*70 + "\n")
        
        return resumen