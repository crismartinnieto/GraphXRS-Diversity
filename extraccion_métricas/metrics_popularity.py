"""
Métricas basadas en popularidad
"""
from typing import Dict, List
from utils import get_connected_properties, get_business_nodes, build_networkx_graph

def attribute_popularity(subgraph: Dict, property_type: str, property_value: str) -> int:
    """
    Cuántos hoteles del KG están conectados a ese atributo.
    Popularity(p) = degree(p)
    """
    all_hotels = get_business_nodes(subgraph)
    count = 0
    
    for hotel_id in all_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        if property_value in props.get(property_type, []):
            count += 1
    
    return count

def attribute_popularity_rank(subgraph: Dict, property_type: str, property_value: str) -> float:
    """
    Percentil del atributo entre todos (ranking normalizado).
    """
    from utils import get_all_user_properties
    
    all_hotels = get_business_nodes(subgraph)
    
    # Obtener todas las propiedades únicas y sus popularidades
    all_props = {}
    for hotel_id in all_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        for rel_type, values in props.items():
            for val in values:
                key = f"{rel_type}:{val}"
                all_props[key] = all_props.get(key, 0) + 1
    
    # Popularidad de la propiedad actual
    current_key = f"{property_type}:{property_value}"
    current_pop = all_props.get(current_key, 0)
    
    # Ranking: cuántas propiedades son menos populares
    less_popular = sum(1 for pop in all_props.values() if pop < current_pop)
    
    if len(all_props) == 0:
        return 0.0
    
    return less_popular / len(all_props)

def inverse_popularity(subgraph: Dict, property_type: str, property_value: str) -> float:
    """
    IP(p) = 1 / Popularity(p)
    Mayor valor = más inesperado/raro
    """
    pop = attribute_popularity(subgraph, property_type, property_value)
    if pop == 0:
        return 0.0
    return 1.0 / pop

def commonality_score(subgraph: Dict, property_type: str, property_value: str) -> int:
    """
    Cuántos usuarios de la base usan ese atributo en consumos previos.
    NOTA: Esto requiere grafo de interacción completo, no disponible en subgrafo.
    Retornamos 0 como placeholder.
    """
    # Esta métrica necesita acceso a todos los usuarios, no solo el subgrafo
    # Se debería calcular a nivel global con acceso a Neo4j
    return 0

def compute_all_popularity_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                   consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas de popularidad.
    
    Returns:
        Lista de dicts con métricas por cada propiedad del hotel recomendado
    """
    results = []
    
    rec_props = get_connected_properties(subgraph, hotel_rec_id)
    
    for rel_type, values in rec_props.items():
        for prop_value in values:
            pop = attribute_popularity(subgraph, rel_type, prop_value)
            rank = attribute_popularity_rank(subgraph, rel_type, prop_value)
            inv_pop = inverse_popularity(subgraph, rel_type, prop_value)
            common = commonality_score(subgraph, rel_type, prop_value)
            
            result = {
                'usuario': user_id,
                'hotel_recomendado': hotel_rec_id,
                'propiedad': f"{rel_type}:{prop_value}",
                'hotel_consumido': None,
                'attribute_popularity': pop,
                'attribute_popularity_rank': rank,
                'inverse_popularity': inv_pop,
                'commonality_score': common
            }
            results.append(result)
    
    return results