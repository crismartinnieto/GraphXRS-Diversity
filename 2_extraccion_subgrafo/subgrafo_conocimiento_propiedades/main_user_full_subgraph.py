import os
from utils_interactions import get_user_interacted_hotels
from utils_knowledge import get_subgraph_for_hotels
from save_graph import save_full_subgraph_to_json  
import time
import pandas as pd

def extract_user_subgraph(user_id: int, recommended_hotels: list):
    """
    Extrae un subgrafo para un usuario incluyendo:
    - Hoteles previos
    - Lista de hoteles recomendados
    """

    start_time = time.time()

    # Hoteles previos del usuario
    user_hotels = get_user_interacted_hotels(user_id)
    print(f"Hoteles previos del usuario {user_id}: {user_hotels}")

    # Combinar hoteles previos + recomendados
    hotel_ids = list(set(user_hotels + recommended_hotels))
    print(f"Total de hoteles a incluir en el subgrafo: {hotel_ids}")

    # Obtener nodos y relaciones
    nodes, relationships = get_subgraph_for_hotels(hotel_ids)
    print(f"Nodos encontrados: {len(nodes)}, Relaciones: {len(relationships)}")

    # Guardar en JSON
    filename = f"user_{user_id}_full_subgraph.json"
    save_path = save_full_subgraph_to_json(nodes, relationships, filename)

    end_time = time.time()
    print(f"⏱️ Tiempo total: {end_time - start_time:.4f} segundos")

    return save_path



     
#SI QUEREMOS 
if __name__ == "__main__":
     # Ruta a tu CSV
    csv_path = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\data_recommender\relacion_usuario_rating_recomendador.csv"
    
    # Leer CSV
    df = pd.read_csv(csv_path)
    
    # Agrupar por usuario
    for user_id, group in df.groupby('usuario'):
        recommended_hotels = group['negocio'].tolist()
        print(f"\nProcesando subgrafo completo del usuario {user_id}...")
        extract_user_subgraph(user_id, recommended_hotels)

