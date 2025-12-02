# config.py
# Ajusta aquí las rutas si cambian en tu máquina.

INPUT_SUBGRAPHS_DIR = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\extraccion_subgrafo\data\subgrafos"
OUTPUT_DIR = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\extraccion_métricas\csv_explicabilidad"
DETAILED_CSV_NAME = "explanations_detailed_rows.csv"
AGGREGATED_CSV_NAME = "explanations_aggregated_per_rec.csv"

# Parámetros de cómputo (puedes ajustar)
TOP_K_EXAMPLES = 3   # para métricas tipo k-NN example strength
WEIGHTS_BY_TYPE = {
    "located_in_city": 3.0,
    "has_category": 2.0,
    "has_attribute": 1.0,
    "has_rating": 1.5,
    "has_postal_code": 1.0
}

# Control de performance: si True, calculamos métricas más costosas (betweenness, eigenvector)
COMPUTE_EXPENSIVE_CENTRALITIES = True
