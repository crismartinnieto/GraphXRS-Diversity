"""
Módulo para cargar y validar datos del sistema de recomendación XAI
"""
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional


class DataLoader:
    """
    Clase para cargar los datos de recomendaciones y explicaciones
    """
    
    def __init__(self, 
                 recomendaciones_path: str,
                 explicaciones_path: str):
        """
        Args:
            recomendaciones_path: Ruta al CSV con usuarios y hoteles recomendados
            explicaciones_path: Ruta al CSV con propiedades compartidas (explicaciones)
        """
        self.recomendaciones_path = Path(recomendaciones_path)
        self.explicaciones_path = Path(explicaciones_path)
        
        self.df_recomendaciones: Optional[pd.DataFrame] = None
        self.df_explicaciones: Optional[pd.DataFrame] = None
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Carga ambos datasets y realiza validaciones básicas
        
        Returns:
            Tupla con (df_recomendaciones, df_explicaciones)
        """
        # Cargar recomendaciones
        if not self.recomendaciones_path.exists():
            raise FileNotFoundError(f"No se encontró: {self.recomendaciones_path}")
        
        self.df_recomendaciones = pd.read_csv(self.recomendaciones_path)
        print(f"✓ Recomendaciones cargadas: {len(self.df_recomendaciones)} filas")
        
        # Cargar explicaciones
        if not self.explicaciones_path.exists():
            raise FileNotFoundError(f"No se encontró: {self.explicaciones_path}")
        
        self.df_explicaciones = pd.read_csv(self.explicaciones_path)
        print(f"✓ Explicaciones cargadas: {len(self.df_explicaciones)} filas")
        
        # Validar estructura
        self._validate_data()
        
        return self.df_recomendaciones, self.df_explicaciones
    
    def _validate_data(self):
        """
        Valida que los DataFrames tengan las columnas esperadas
        """
        # Validar recomendaciones
        required_rec_cols = {'user', 'hotel_recomendado'}
        rec_cols = set(self.df_recomendaciones.columns)
        
        if not required_rec_cols.issubset(rec_cols):
            missing = required_rec_cols - rec_cols
            raise ValueError(f"Faltan columnas en recomendaciones: {missing}")
        
        # Validar explicaciones
        required_exp_cols = {'user', 'hotel_recomendado', 'hotel_ejemplo_id', 
                            'numero_propiedades', 'lista_propiedades'}
        exp_cols = set(self.df_explicaciones.columns)
        
        if not required_exp_cols.issubset(exp_cols):
            missing = required_exp_cols - exp_cols
            raise ValueError(f"Faltan columnas en explicaciones: {missing}")
        
        print("✓ Validación de estructura completada")
    
    def get_user_recommendations(self, user_id: int) -> pd.DataFrame:
        """
        Obtiene todas las recomendaciones para un usuario específico
        
        Args:
            user_id: ID del usuario
            
        Returns:
            DataFrame filtrado por usuario
        """
        return self.df_recomendaciones[
            self.df_recomendaciones['user'] == user_id
        ]
    
    def get_user_explanations(self, user_id: int, hotel_id: str) -> pd.DataFrame:
        """
        Obtiene las explicaciones para un par usuario-hotel
        
        Args:
            user_id: ID del usuario
            hotel_id: ID del hotel recomendado
            
        Returns:
            DataFrame con explicaciones (propiedades compartidas)
        """
        return self.df_explicaciones[
            (self.df_explicaciones['user'] == user_id) &
            (self.df_explicaciones['hotel_recomendado'] == hotel_id)
        ]