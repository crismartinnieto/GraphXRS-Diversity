"""
Sistema XAI para Evaluación de Explicabilidad en Recomendaciones de Hoteles
Autor: Cristina
TFM MUSII
"""

__version__ = "1.0.0"
__author__ = "Cristina"

# Importaciones principales para facilitar el uso
from .data_loader import DataLoader
from .pipeline import XAICoveragePipeline

__all__ = [
    'DataLoader',
    'XAICoveragePipeline'
]