import os
from utils_interactions import get_user_interacted_hotels
from utils_knowledge import get_subgraph_for_hotels
from save_graph import save_subgraph_to_json  
import time
import pandas as pd

def extract_user_subgraph(user_id: int, recommended_hotel: int):
    """
    Proceso completo:
    1. Obtiene hoteles con los que ya interactuó el usuario.
    2. Forma un conjunto: [hotel_recomendado + interacciones previas]
    3. Extrae el subgrafo del grafo de conocimiento.
    4. Lo guarda en un archivo JSON dentro de data/subgrafos.
    """

    start_time = time.time()

    # 1. Interacciones del usuario
    user_hotels = get_user_interacted_hotels(user_id)
    print(f"Hoteles previos del usuario {user_id}: {user_hotels}")

    # 2. Lista total de interés
    hotel_ids = list(set([recommended_hotel] + user_hotels))
    print(f"Hoteles a incluir en el subgrafo: {hotel_ids}")

    # 3. Obtener nodos y relaciones del grafo de conocimiento
    nodes, relationships = get_subgraph_for_hotels(hotel_ids)
    print(f"Nodos encontrados: {len(nodes)}, Relaciones: {len(relationships)}")

    # 4. Guardado en JSON
    filename = f"user_{user_id}_hotel_{recommended_hotel}.json"
    save_path = save_subgraph_to_json(nodes, relationships, filename)

    end_time = time.time()  
    elapsed = end_time - start_time
    print(f"⏱️ Tiempo total: {elapsed:.4f} segundos")

    return save_path


# SI QUEREMOS SACAR UN USUARIO Y HOTEL CONCRETO
# if __name__ == "__main__": 
#     extract_user_subgraph(user_id=3, recommended_hotel=2963)

# SI QUEREMOS SACAR TODOS LOS USUARIOS Y HOTELES. PERO CADA SUBGRAFO ES UNA COMBINACION DE UN USUARIO Y UN HOTEL
# if __name__ == "__main__":
#     csv_path = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\data_recommender\relacion_usuario_rating_recomendador.csv"
#     df = pd.read_csv(csv_path)
#     for idx, row in df.iterrows():
#         user_id = int(row['usuario'])
#         recommended_hotel = int(row['negocio'])
#         extract_user_subgraph(user_id, recommended_hotel)

