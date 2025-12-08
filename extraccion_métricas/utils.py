"""
Funciones utilitarias para procesamiento de subgrafos
"""
import json
import networkx as nx
import math
from typing import Dict, List, Set, Tuple
from config import BUSINESS_LABELS

def load_subgraph(filepath: str) -> Dict:
    """Carga un subgrafo desde archivo JSON"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_filename(filename: str) -> Tuple[int, str]:
    """
    Extrae user_id y hotel_id del nombre de archivo.
    Ejemplo: user_3_hotel_25.json -> (3, '25')
    """
    parts = filename.replace('.json', '').split('_')
    user_id = int(parts[1])
    hotel_id = parts[3]
    return user_id, hotel_id

def get_business_nodes(subgraph: Dict) -> List[str]:
    """Obtiene los IDs de todos los nodos tipo Business"""
    business_nodes = []
    for node in subgraph['nodes']:
        labels = node.get('labels', [])
        if any(label in BUSINESS_LABELS for label in labels):
            business_nodes.append(node['id'])
    return business_nodes

def identify_recommended_hotel(subgraph: Dict, hotel_id_from_file: str) -> str:
    """
    Identifica el hotel recomendado en el subgrafo.
    Busca el Business cuyo properties.id coincide con hotel_id_from_file
    """
    for node in subgraph['nodes']:
        labels = node.get('labels', [])
        if any(label in BUSINESS_LABELS for label in labels):
            props = node.get('properties', {})
            if props.get('id') == hotel_id_from_file:
                return node['id']
    return None

def get_user_consumed_hotels(subgraph: Dict, hotel_rec_id: str) -> List[str]:
    """
    Obtiene los hoteles consumidos por el usuario.
    Son todos los Business del subgrafo excepto el recomendado.
    """
    all_business = get_business_nodes(subgraph)
    consumed = [h for h in all_business if h != hotel_rec_id]
    return consumed

def get_connected_properties(subgraph: Dict, hotel_id: str) -> Dict[str, List[str]]:
    """
    Obtiene todas las propiedades conectadas a un hotel.
    
    Returns:
        Dict: {relation_type: [values]}
        Ejemplo: {'has_category': ['Tours', 'Museums'], 'located_in_city': ['Philadelphia']}
    """
    properties = {}
    
    for rel in subgraph['relationships']:
        if rel['start_node'] == hotel_id:
            rel_type = rel['properties'].get('type')
            end_node_id = rel['end_node']
            
            # Buscar el valor de la propiedad en los nodos
            for node in subgraph['nodes']:
                if node['id'] == end_node_id:
                    value = node.get('properties', {}).get('name')
                    if value:
                        if rel_type not in properties:
                            properties[rel_type] = []
                        properties[rel_type].append(value)
                    break
    
    return properties

def get_all_properties_flat(subgraph: Dict, hotel_id: str) -> Set[str]:
    """
    Obtiene todas las propiedades de un hotel como un set plano.
    Útil para operaciones de intersección/unión.
    """
    props = get_connected_properties(subgraph, hotel_id)
    flat_props = set()
    for values in props.values():
        flat_props.update(values)
    return flat_props

def get_all_user_properties(subgraph: Dict, consumed_hotels: List[str]) -> Dict[str, Set[str]]:
    """
    Obtiene todas las propiedades únicas consumidas por el usuario.
    
    Returns:
        Dict: {relation_type: {values}}
    """
    user_props = {}
    
    for hotel_id in consumed_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        for rel_type, values in props.items():
            if rel_type not in user_props:
                user_props[rel_type] = set()
            user_props[rel_type].update(values)
    
    return user_props

def get_shared_properties(subgraph: Dict, hotel1: str, hotel2: str) -> Dict[str, List[str]]:
    """
    Obtiene las propiedades compartidas entre dos hoteles.
    
    Returns:
        Dict: {relation_type: [shared_values]}
    """
    props1 = get_connected_properties(subgraph, hotel1)
    props2 = get_connected_properties(subgraph, hotel2)
    
    shared = {}
    for rel_type, values1 in props1.items():
        if rel_type in props2:
            values2 = props2[rel_type]
            intersection = list(set(values1) & set(values2))
            if intersection:
                shared[rel_type] = intersection
    
    return shared

def jaccard_similarity(set1: Set, set2: Set) -> float:
    """
    Similitud de Jaccard entre dos conjuntos.
    J(A,B) = |A ∩ B| / |A ∪ B|
    """
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0

def cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """
    Similitud coseno entre dos vectores (diccionarios).
    cos(A,B) = (A·B) / (||A|| ||B||)
    """
    # Claves comunes
    common_keys = set(vec1.keys()) & set(vec2.keys())
    
    if not common_keys:
        return 0.0
    
    # Producto punto
    dot_product = sum(vec1[k] * vec2[k] for k in common_keys)
    
    # Normas
    norm1 = math.sqrt(sum(v**2 for v in vec1.values()))
    norm2 = math.sqrt(sum(v**2 for v in vec2.values()))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def build_networkx_graph(subgraph: Dict) -> nx.Graph:
    """
    Construye un grafo de NetworkX desde el subgrafo JSON.
    """
    G = nx.Graph()
    
    # Añadir nodos
    for node in subgraph['nodes']:
        G.add_node(node['id'], **node.get('properties', {}))
    
    # Añadir aristas
    for rel in subgraph['relationships']:
        G.add_edge(
            rel['start_node'], 
            rel['end_node'],
            relation_type=rel['properties'].get('type')
        )
    
    return G

def get_node_by_property(subgraph: Dict, property_value: str) -> str:
    """
    Busca el ID de un nodo por su valor de propiedad 'name'.
    """
    for node in subgraph['nodes']:
        if node.get('properties', {}).get('name') == property_value:
            return node['id']
    return None

def get_business_property_id(subgraph: Dict, node_id: str) -> str:
    """
    Obtiene el ID del negocio (properties.id) dado un node_id.
    
    Args:
        node_id: ID interno del nodo en el grafo
        
    Returns:
        El valor de properties.id del negocio, o None si no se encuentra
    """
    for node in subgraph['nodes']:
        if node['id'] == node_id:
            labels = node.get('labels', [])
            if any(label in BUSINESS_LABELS for label in labels):
                return node.get('properties', {}).get('id')
    return None