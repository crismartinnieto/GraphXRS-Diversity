"""
Configuración global del sistema de métricas de explicabilidad
"""

# Rutas principales
SUBGRAPHS_DIR = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\extraccion_subgrafo\data\subgrafos"
OUTPUT_DIR = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\extraccion_métricas\csv_explicabilidad\subgrafos"

# Pesos para métricas ponderadas
WEIGHTS = {
    # Tipos de relaciones
    'located_in_city': 3.0,
    'in_state': 2.5,
    'has_category': 2.0,
    'has_rating': 1.5,
    'has_coordinates': 1.0,
    'has_postal_code': 1.0,
    'has_attribute': 1.0,
    'has_name': 0.5,
    'has_review_count': 0.8,
    'status': 0.3
}

# Tipos de relaciones agrupadas semánticamente
RELATION_TYPES = {
    'location': ['located_in_city', 'in_state', 'has_postal_code', 'has_coordinates'],
    'category': ['has_category'],
    'quality': ['has_rating', 'has_review_count'],
    'attribute': ['has_attribute'],
    'identity': ['has_name', 'status']
}

# Configuración de NetworkX para centralidad
CENTRALITY_CONFIG = {
    'betweenness_normalized': True,
    'closeness_normalized': True,
    'pagerank_alpha': 0.85,
    'pagerank_max_iter': 100
}

# Configuración de similitud
SIMILARITY_CONFIG = {
    'k_nearest': 5  # Para k-Nearest Example Strength
}

# Estructura de columnas para CSVs
CSV_COLUMNS_BASE = ['usuario', 'hotel_recomendado', 'propiedad', 'hotel_consumido']
CSV_COLUMNS_GLOBAL = ['usuario', 'hotel_recomendado']  # Para métricas globales

# Tipos de nodos que representan negocios/hoteles
BUSINESS_LABELS = ['Business']