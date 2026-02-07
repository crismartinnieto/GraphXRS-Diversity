import json
import os
import csv
from pathlib import Path

def extract_business_properties(nodes, relationships, business_id):
    """
    Extrae todas las propiedades de un negocio específico.
    Retorna un diccionario con las propiedades del negocio.
    """
    properties = {
        'name': None,
        'city': None,
        'state': None,
        'postal_code': None,
        'rating': None,
        'review_count': None,
        'categories': [],
        'attributes': [],
        'coordinates': None
    }
    
    # Crear un mapa de nodos para acceso rápido
    node_map = {node['id']: node for node in nodes}
    
    # Buscar todas las relaciones del negocio
    for rel in relationships:
        if rel['start_node'] == business_id:
            rel_type = rel['properties']['type']
            end_node = node_map.get(rel['end_node'])
            
            if not end_node:
                continue
                
            node_name = end_node['properties'].get('name', '')
            
            if rel_type == 'has_name':
                properties['name'] = node_name
            elif rel_type == 'located_in_city':
                properties['city'] = node_name
            elif rel_type == 'in_state':
                properties['state'] = node_name
            elif rel_type == 'has_postal_code':
                properties['postal_code'] = node_name
            elif rel_type == 'has_rating':
                properties['rating'] = node_name
            elif rel_type == 'has_review_count':
                properties['review_count'] = node_name
            elif rel_type == 'has_category':
                properties['categories'].append(node_name)
            elif rel_type == 'has_attribute':
                properties['attributes'].append(node_name)
            elif rel_type == 'has_coordinates':
                properties['coordinates'] = node_name
    
    return properties

def get_all_properties_list(properties):
    """
    Convierte el diccionario de propiedades en una lista de strings formateados.
    """
    props_list = []
    
    if properties['city']:
        props_list.append(f"city:{properties['city']}")
    if properties['state']:
        props_list.append(f"state:{properties['state']}")
    if properties['postal_code']:
        props_list.append(f"postal_code:{properties['postal_code']}")
    if properties['rating']:
        props_list.append(f"rating:{properties['rating']}")
    if properties['review_count']:
        props_list.append(f"review_count:{properties['review_count']}")
    
    for cat in properties['categories']:
        props_list.append(f"category:{cat}")
    
    for attr in properties['attributes']:
        props_list.append(f"attribute:{attr}")
    
    if properties['coordinates']:
        props_list.append(f"coordinates:{properties['coordinates']}")
    
    return props_list

def find_shared_properties(props1, props2):
    """
    Encuentra las propiedades compartidas entre dos hoteles.
    Retorna una lista de propiedades compartidas.
    """
    shared = []
    
    # Comparar propiedades simples
    if props1['city'] and props1['city'] == props2['city']:
        shared.append(f"city:{props1['city']}")
    
    if props1['state'] and props1['state'] == props2['state']:
        shared.append(f"state:{props1['state']}")
    
    if props1['postal_code'] and props1['postal_code'] == props2['postal_code']:
        shared.append(f"postal_code:{props1['postal_code']}")
    
    if props1['rating'] and props1['rating'] == props2['rating']:
        shared.append(f"rating:{props1['rating']}")
    
    # Comparar categorías
    common_categories = set(props1['categories']) & set(props2['categories'])
    for cat in common_categories:
        shared.append(f"category:{cat}")
    
    # Comparar atributos
    common_attributes = set(props1['attributes']) & set(props2['attributes'])
    for attr in common_attributes:
        shared.append(f"attribute:{attr}")
    
    return shared

def process_subgraph_file(filepath):
    """
    Procesa un archivo JSON de subgrafo y extrae la información relevante.
    """
    # Extraer user_id y hotel_id del nombre del archivo
    filename = os.path.basename(filepath)
    # Formato: user_X_hotel_Y.json
    parts = filename.replace('.json', '').split('_')
    user_id = parts[1]
    hotel_recomendado_id = parts[3]
    
    # Cargar el JSON
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    nodes = data['nodes']
    relationships = data['relationships']
    
    # Identificar todos los negocios en el grafo
    business_nodes = [node for node in nodes if 'Business' in node['labels']]
    
    # Separar el hotel recomendado de los hoteles ejemplo
    hotel_recomendado = None
    hoteles_ejemplo = []
    
    for business in business_nodes:
        business_id = business['properties']['id']
        if business_id == hotel_recomendado_id:
            hotel_recomendado = business['id']
        else:
            hoteles_ejemplo.append(business['id'])
    
    if not hotel_recomendado:
        print(f"Warning: Hotel recomendado {hotel_recomendado_id} no encontrado en {filename}")
        return [], []
    
    # Extraer propiedades del hotel recomendado
    props_recomendado = extract_business_properties(nodes, relationships, hotel_recomendado)
    
    # CSV 1: Comparaciones (propiedades compartidas)
    comparisons = []
    # CSV 2: Propiedades individuales de cada hotel histórico
    individual_hotels = []
    
    for hotel_ej in hoteles_ejemplo:
        props_ejemplo = extract_business_properties(nodes, relationships, hotel_ej)
        hotel_ejemplo_business_id = [node['properties']['id'] for node in business_nodes if node['id'] == hotel_ej][0]
        
        # CSV 1: Propiedades compartidas con el recomendado
        shared_props = find_shared_properties(props_recomendado, props_ejemplo)
        comparisons.append({
            'user': user_id,
            'hotel_recomendado': hotel_recomendado_id,
            'hotel_ejemplo_id': hotel_ejemplo_business_id,
            'numero_propiedades': len(shared_props),
            'lista_propiedades': ' | '.join(shared_props) if shared_props else 'Ninguna'
        })
        
        # CSV 2: Todas las propiedades del hotel histórico
        all_props = get_all_properties_list(props_ejemplo)
        individual_hotels.append({
            'user': user_id,
            'hotel_ejemplo_id': hotel_ejemplo_business_id,
            'numero_propiedades': len(all_props),
            'lista_propiedades': ' | '.join(all_props) if all_props else 'Ninguna'
        })
    
    return comparisons, individual_hotels

def main():
    # Opción 1: Usar ruta relativa al script
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    subgrafos_dir = base_dir / 'extraccion_subgrafo' / 'data' / 'subgrafos'
    
    # Opción 2: Si la opción 1 no funciona, usar ruta absoluta
    if not subgrafos_dir.exists():
        subgrafos_dir = Path(r'C:\Users\cris\Desktop\MUSII\TFM\Sistema_recomendacion_xai_TFM_MUSII_CMN\extraccion_subgrafo\data\subgrafos')
    
    # Verificar que existe el directorio
    if not subgrafos_dir.exists():
        print(f"Error: No se encuentra el directorio {subgrafos_dir.absolute()}")
        print(f"\nPor favor, verifica que la ruta sea correcta.")
        return
    
    # Obtener todos los archivos JSON
    json_files = list(subgrafos_dir.glob('*.json'))
    print(f"Encontrados {len(json_files)} archivos JSON")
    
    # Procesar todos los archivos
    all_comparisons = []
    all_individual_hotels = []
    
    for i, json_file in enumerate(json_files, 1):
        print(f"Procesando {i}/{len(json_files)}: {json_file.name}")
        try:
            comparisons, individual_hotels = process_subgraph_file(json_file)
            all_comparisons.extend(comparisons)
            all_individual_hotels.extend(individual_hotels)
        except Exception as e:
            print(f"Error procesando {json_file.name}: {e}")
    
    # Crear directorio de salida si no existe
    output_dir = Path('data_2')
    output_dir.mkdir(exist_ok=True)
    
    # CSV 1: Propiedades compartidas
    output_file1 = output_dir / 'propiedades_compartidas.csv'
    with open(output_file1, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'user',
            'hotel_recomendado',
            'hotel_ejemplo_id',
            'numero_propiedades',
            'lista_propiedades'
        ])
        writer.writeheader()
        writer.writerows(all_comparisons)
    
    # CSV 2: Propiedades individuales de hoteles históricos
    output_file2 = output_dir / 'hoteles_historicos_propiedades.csv'
    with open(output_file2, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'user',
            'hotel_ejemplo_id',
            'numero_propiedades',
            'lista_propiedades'
        ])
        writer.writeheader()
        writer.writerows(all_individual_hotels)
    
    print(f"\n✓ Procesamiento completado!")
    print(f"\n📄 CSVs generados:")
    print(f"  1. {output_file1.name} ({len(all_comparisons)} filas)")
    print(f"  2. {output_file2.name} ({len(all_individual_hotels)} filas)")
    print(f"\n📁 Guardados en: {output_dir.absolute()}")

if __name__ == "__main__":
    main()