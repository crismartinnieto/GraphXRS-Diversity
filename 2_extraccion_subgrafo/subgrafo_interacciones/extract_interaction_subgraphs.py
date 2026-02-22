import os
from utils_interactions_expanded import get_user_recommended_hotels
from utils_interaction_patterns import get_subgraph_for_user_and_hotel
from save_graph import save_subgraph_to_json
import time
import pandas as pd


def extract_user_interaction_subgraph(user_id: int, recommended_hotel: int):
    """
    Extrae subgrafo de INTERACCIONES mostrando cómo usuarios similares 
    conectan al usuario objetivo con el hotel recomendado
    """
    
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"👤 Usuario: {user_id} | 🏨 Hotel recomendado: {recommended_hotel}")
    print(f"{'='*60}")
    
    # Obtener subgrafo
    result = get_subgraph_for_user_and_hotel(user_id, recommended_hotel)
    
    if result is None:
        return None
    
    nodes, relationships = result
    
    print(f"✅ Nodos: {len(nodes)} | Relaciones: {len(relationships)}")
    
    # Guardar
    filename = f"user_{user_id}_hotel_{recommended_hotel}_interactions.json"
    save_path = save_subgraph_to_json(nodes, relationships, filename)
    
    end_time = time.time()
    print(f"⏱️ Tiempo: {end_time - start_time:.2f}s")
    
    return save_path


if __name__ == "__main__":
    # Procesar todas las recomendaciones
    csv_path = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\data_recommender\relacion_usuario_rating_recomendador.csv"
    df = pd.read_csv(csv_path)
    
    print(f"\n🚀 Procesando {len(df)} recomendaciones...\n")
    
    procesados = 0
    fallidos = 0
    
    for idx, row in df.iterrows():
        user_id = int(row['usuario'])
        recommended_hotel = int(row['negocio'])
        
        result = extract_user_interaction_subgraph(user_id, recommended_hotel)
        
        if result:
            procesados += 1
        else:
            fallidos += 1
        
        # Progreso cada 10
        if (idx + 1) % 10 == 0:
            print(f"\n📊 Progreso: {idx + 1}/{len(df)}")
    
    print(f"\n{'='*60}")
    print(f"✅ COMPLETADO")
    print(f"{'='*60}")
    print(f"   ✓ Exitosos: {procesados}")
    print(f"   ✗ Fallidos: {fallidos}")
