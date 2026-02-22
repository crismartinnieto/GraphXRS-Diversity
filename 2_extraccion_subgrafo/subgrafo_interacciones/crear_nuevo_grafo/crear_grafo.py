import pandas as pd
import os

# Rutas de los archivos
csv_historico = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\1_arquitectura_completa\loader\data\grafo_interaccion_datos_train.csv"
csv_recomendaciones = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\data_recommender\relacion_usuario_rating_recomendador.csv"
output_path = r"C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\2_extraccion_subgrafo\subgrafo_interacciones\nuevo_grafo"
output_file = os.path.join(output_path, "grafo_interaccion_con_recomendaciones.csv")

# Crear directorio si no existe
os.makedirs(output_path, exist_ok=True)

print("🔄 Cargando datos...")

# Cargar CSVs
df_historico = pd.read_csv(csv_historico)
df_recomendaciones = pd.read_csv(csv_recomendaciones)

print(f"✅ Histórico cargado: {len(df_historico)} interacciones")
print(f"✅ Recomendaciones cargadas: {len(df_recomendaciones)} predicciones")

# Lista para almacenar el nuevo grafo
nuevo_grafo = []

# Obtener usuarios únicos del CSV de recomendaciones
usuarios_objetivo = df_recomendaciones['usuario'].unique()

print(f"\n🎯 Procesando {len(usuarios_objetivo)} usuarios...")

for idx, user_id in enumerate(usuarios_objetivo, 1):
    if idx % 10 == 0:
        print(f"   Procesando usuario {idx}/{len(usuarios_objetivo)}...")
    
    # 1️⃣ AÑADIR HISTÓRICOS DEL USUARIO (con rating original)
    historicos_usuario = df_historico[df_historico['user_id'] == user_id]
    for _, row in historicos_usuario.iterrows():
        nuevo_grafo.append({
            'user_id': row['user_id'],
            'business_id': row['business_id'],
            'rating': row['rating']
        })
    
    # 2️⃣ AÑADIR RECOMENDACIONES DEL USUARIO (con rating = 1.0)
    recomendaciones_usuario = df_recomendaciones[df_recomendaciones['usuario'] == user_id]
    for _, row in recomendaciones_usuario.iterrows():
        nuevo_grafo.append({
            'user_id': user_id,
            'business_id': row['negocio'],
            'rating': 10.0
        })
        
        # 3️⃣ EXPANDIR: Añadir otros usuarios que tienen este hotel recomendado en su histórico
        hotel_recomendado = row['negocio']
        usuarios_con_este_hotel = df_historico[df_historico['business_id'] == hotel_recomendado]
        
        for _, hist_row in usuarios_con_este_hotel.iterrows():
            # Solo añadir si no es el mismo usuario objetivo
            if hist_row['user_id'] != user_id:
                nuevo_grafo.append({
                    'user_id': hist_row['user_id'],
                    'business_id': hist_row['business_id'],
                    'rating': hist_row['rating']
                })

print(f"\n📊 Grafo expandido creado: {len(nuevo_grafo)} interacciones")

# Convertir a DataFrame
df_nuevo_grafo = pd.DataFrame(nuevo_grafo)

# Eliminar duplicados (misma combinación user_id + business_id)
print("🧹 Eliminando duplicados...")
df_nuevo_grafo = df_nuevo_grafo.drop_duplicates(subset=['user_id', 'business_id'], keep='first')

print(f"✅ Grafo final: {len(df_nuevo_grafo)} interacciones únicas")

# Guardar CSV
df_nuevo_grafo.to_csv(output_file, index=False)

print(f"\n✅ ¡LISTO! Archivo guardado en:\n{output_file}")

# Mostrar estadísticas
print("\n📈 ESTADÍSTICAS DEL NUEVO GRAFO:")
print(f"   - Total usuarios: {df_nuevo_grafo['user_id'].nunique()}")
print(f"   - Total hoteles: {df_nuevo_grafo['business_id'].nunique()}")
print(f"   - Total interacciones: {len(df_nuevo_grafo)}")
print(f"   - Rating promedio: {df_nuevo_grafo['rating'].mean():.2f}")