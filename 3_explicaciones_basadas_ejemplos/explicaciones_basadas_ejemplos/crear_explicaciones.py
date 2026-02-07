import json
import os
import pandas as pd
from pathlib import Path
from collections import defaultdict

def extraer_propiedades_hotel(nodes, relationships, hotel_node_id):
    propiedades = set()

    for rel in relationships:
        if rel['start_node'] == hotel_node_id:

            rel_type = rel.get('properties', {}).get('type')

            for node in nodes:
                if node['id'] == rel['end_node']:
                    if 'name' in node['properties']:
                        valor = node['properties']['name']
                        tipo = rel_type
                        propiedades.add((valor, tipo))
                    break

    return propiedades


def procesar_subgrafo(json_path):
    """
    Procesa un archivo JSON de subgrafo y extrae la información necesaria.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    nodes = data['nodes']
    relationships = data['relationships']
    
    # Extraer usuario y hotel recomendado del nombre del archivo
    filename = os.path.basename(json_path)
    # Formato: user_X_hotel_Y.json (CORREGIDO: era usuario_X_hotel_Y.json)
    parts = filename.replace('.json', '').split('_')
    usuario_id = parts[1]  # Solo el número
    hotel_recomendado_id = parts[3]  # Solo el número
    
    # Identificar todos los hoteles (nodos tipo Business)
    hoteles = [node for node in nodes if 'Business' in node['labels']]
    
    # Separar hotel recomendado de hoteles históricos
    hotel_rec = None
    hoteles_historicos = []
    
    for hotel in hoteles:
        # Extraer el ID del hotel de sus propiedades
        hotel_id_prop = hotel['properties'].get('id')
        
        # Verificar si es el hotel recomendado
        if hotel_id_prop == hotel_recomendado_id:
            hotel_rec = {
                'id': hotel_id_prop,
                'propiedades': extraer_propiedades_hotel(nodes, relationships, hotel['id'])
            }
        else:
            hoteles_historicos.append({
                'id': hotel_id_prop,
                'propiedades': extraer_propiedades_hotel(nodes, relationships, hotel['id'])
            })
    
    return usuario_id, hotel_rec, hoteles_historicos

def crear_csv_comparacion(datos_usuario, usuario_id, output_path):
    """
    Crea el CSV con comparación entre hoteles históricos y recomendado para un usuario.
    """
    filas = []
    
    for _, hotel_rec, hoteles_hist in datos_usuario:
        for hotel_hist in hoteles_hist:
            # Calcular propiedades compartidas
            props_compartidas = hotel_rec['propiedades'].intersection(hotel_hist['propiedades'])
            
            filas.append({
                'usuario': usuario_id,
                'hotel_recomendado': hotel_rec['id'],
                'hotel_historico': hotel_hist['id'],
                'num_propiedades_compartidas': len(props_compartidas),
                'propiedades_compartidas': list(sorted(props_compartidas))
            })
    
    df = pd.DataFrame(filas)
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"  ✓ CSV de comparación creado: {output_path.name}")
    print(f"    Registros: {len(df)}")
    return len(df)

def crear_csv_historicos(datos_usuario, usuario_id, output_path):
    """
    Crea el CSV con información de hoteles históricos para un usuario.
    """
    # Usar un set para evitar duplicados (basado en usuario + hotel_historico)
    hoteles_unicos = {}
    
    for _, hotel_rec, hoteles_hist in datos_usuario:
        for hotel_hist in hoteles_hist:
            hotel_id = hotel_hist['id']
            # Solo agregar si no existe ya este hotel para este usuario
            if hotel_id not in hoteles_unicos:
                hoteles_unicos[hotel_id] = {
                    'usuario': usuario_id,
                    'hotel_historico': hotel_id,
                    'num_propiedades': len(hotel_hist['propiedades']),
                    'propiedades': list(sorted(hotel_hist['propiedades']))
                }
    
    # Convertir a lista de filas
    filas = list(hoteles_unicos.values())
    
    df = pd.DataFrame(filas)
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"  ✓ CSV de históricos creado: {output_path.name}")
    print(f"    Registros: {len(df)}")
    return len(df)

def main():
    print("="*80)
    print("INICIANDO PROCESO DE GENERACIÓN DE EXPLICACIONES")
    print("="*80)
    
    # ===== CONFIGURACIÓN DE RUTAS =====
    # Este script está en: 3_explicaciones_basadas_ejemplos/explicaciones_basadas_ejemplos/
    script_dir = Path(__file__).resolve().parent
    print(f"\n📁 Directorio del script: {script_dir}")
    
    # Subir 2 niveles para llegar a la raíz del proyecto
    project_root = script_dir.parent.parent
    print(f"📁 Raíz del proyecto: {project_root}")
    
    # Ruta a los subgrafos (entrada)
    subgrafos_dir = project_root / '2_extraccion_subgrafo' / 'data' / 'subgrafos'
    print(f"📂 Directorio de subgrafos: {subgrafos_dir}")
    
    # Ruta de salida (mismo nivel que el script)
    explicaciones_dir = script_dir / 'data'
    print(f"💾 Directorio de salida: {explicaciones_dir}")
    
    # ===== VERIFICACIÓN DE DIRECTORIOS =====
    if not subgrafos_dir.exists():
        print(f"\n❌ ERROR: No existe el directorio de subgrafos: {subgrafos_dir}")
        print("   Verifica la estructura del proyecto.")
        return
    
    # Crear directorio de salida si no existe
    explicaciones_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Directorio de salida creado/verificado")
    
    # ===== PROCESAMIENTO DE SUBGRAFOS =====
    print("\n" + "="*80)
    print("PROCESANDO SUBGRAFOS...")
    print("="*80)
    
    datos_por_usuario = defaultdict(list)
    
    json_files = list(subgrafos_dir.glob('*.json'))
    print(f"\n📊 Encontrados {len(json_files)} archivos JSON en total\n")
    
    if len(json_files) == 0:
        print("❌ No se encontraron archivos JSON en el directorio de subgrafos")
        print(f"   Ruta verificada: {subgrafos_dir}")
        return
    
    # Procesar cada archivo
    procesados = 0
    errores = 0
    
    for json_file in json_files:
        try:
            usuario_id, hotel_rec, hoteles_hist = procesar_subgrafo(json_file)
            datos_por_usuario[usuario_id].append((usuario_id, hotel_rec, hoteles_hist))
            print(f"  ✓ Procesado: {json_file.name} (Usuario {usuario_id})")
            procesados += 1
        except Exception as e:
            print(f"  ✗ Error en {json_file.name}: {str(e)}")
            errores += 1
    
    print(f"\n📈 Resumen del procesamiento:")
    print(f"   ✓ Archivos procesados: {procesados}")
    print(f"   ✗ Archivos con error: {errores}")
    
    if not datos_por_usuario:
        print("\n❌ No se procesaron archivos correctamente. Verifica la estructura de los JSON.")
        return
    
    print(f"\n👥 Total de usuarios únicos: {len(datos_por_usuario)}")
    print(f"📊 Total de subgrafos procesados: {sum(len(v) for v in datos_por_usuario.values())}")
    
    # ===== GENERACIÓN DE CSVs =====
    print("\n" + "="*80)
    print("GENERANDO CSVs POR USUARIO...")
    print("="*80)
    
    total_registros_comp = 0
    total_registros_hist = 0
    
    for usuario_id, datos_usuario in datos_por_usuario.items():
        print(f"\n👤 Usuario {usuario_id}:")
        
        # CSV de comparación
        output_comp = explicaciones_dir / f'explicaciones_usuario_{usuario_id}_hotel_his_y_rec.csv'
        registros_comp = crear_csv_comparacion(datos_usuario, usuario_id, output_comp)
        total_registros_comp += registros_comp
        
        # CSV de históricos
        output_hist = explicaciones_dir / f'explicaciones_usuario_{usuario_id}_hotel_his.csv'
        registros_hist = crear_csv_historicos(datos_usuario, usuario_id, output_hist)
        total_registros_hist += registros_hist
    
    # ===== RESUMEN FINAL =====
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO EXITOSAMENTE")
    print("="*80)
    print(f"\n📂 CSVs generados en: {explicaciones_dir}")
    print(f"\n📊 Estadísticas:")
    print(f"   • Total registros en CSVs de comparación: {total_registros_comp}")
    print(f"   • Total registros en CSVs de históricos: {total_registros_hist}")
    print(f"   • Usuarios procesados: {len(datos_por_usuario)}")
    
    # Listar archivos generados
    print(f"\n📄 Archivos generados:")
    csv_files = sorted(explicaciones_dir.glob('*.csv'))
    for csv_file in csv_files:
        size_kb = csv_file.stat().st_size / 1024
        print(f"   • {csv_file.name} ({size_kb:.1f} KB)")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()