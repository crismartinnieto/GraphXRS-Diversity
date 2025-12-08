"""
Métricas basadas en novedad/serendipia/surprise
"""
from typing import Dict, List
from utils import (get_all_properties_flat, get_all_user_properties, 
                   get_connected_properties, get_business_nodes)

def novelty_count(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> int:
    """
    Número de atributos nuevos para el usuario en el recomendado.
    NoveltyCount = |Props(rec) - Props(cons)|
    """
    rec_props = get_all_properties_flat(subgraph, hotel_rec)
    user_props_dict = get_all_user_properties(subgraph, consumed_hotels)
    user_props = set()
    for values in user_props_dict.values():
        user_props.update(values)
    
    novelty = rec_props - user_props
    return len(novelty)

def novelty_ratio(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Proporción de atributos nuevos en el recomendado.
    NoveltyRatio = |Props(rec) - Props(cons)| / |Props(rec)|
    """
    rec_props = get_all_properties_flat(subgraph, hotel_rec)
    
    if not rec_props:
        return 0.0
    
    nc = novelty_count(subgraph, consumed_hotels, hotel_rec)
    return nc / len(rec_props)

def surprise_score(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Score de sorpresa: combina novedad con rareza (inversa de popularidad).
    Surprise = NoveltyRatio × promedio(IP(p)) para p nuevos
    """
    from metrics_popularity import inverse_popularity
    
    rec_props = get_connected_properties(subgraph, hotel_rec)
    user_props_dict = get_all_user_properties(subgraph, consumed_hotels)
    user_props_flat = set()
    for values in user_props_dict.values():
        user_props_flat.update(values)
    
    # Propiedades nuevas
    new_props = []
    for rel_type, values in rec_props.items():
        for val in values:
            if val not in user_props_flat:
                new_props.append((rel_type, val))
    
    if not new_props:
        return 0.0
    
    # Calcular IP promedio de propiedades nuevas
    avg_ip = 0.0
    for rel_type, val in new_props:
        ip = inverse_popularity(subgraph, rel_type, val)
        avg_ip += ip
    
    avg_ip /= len(new_props)
    
    # Surprise = NoveltyRatio × IP_promedio
    nr = novelty_ratio(subgraph, consumed_hotels, hotel_rec)
    return nr * avg_ip

def compute_all_novelty_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas de novedad.
    
    Returns:
        Lista con una sola fila (métricas globales)
    """
    nc = novelty_count(subgraph, consumed_hotels, hotel_rec_id)
    nr = novelty_ratio(subgraph, consumed_hotels, hotel_rec_id)
    surprise = surprise_score(subgraph, consumed_hotels, hotel_rec_id)
    
    result = {
        'usuario': user_id,
        'hotel_recomendado': hotel_rec_id,
        'hotel_consumido': None,
        'propiedad': None,
        'novelty_count': nc,
        'novelty_ratio': nr,
        'surprise_score': surprise
    }
    
    return [result]