"""
Métricas basadas en similitud
"""
from typing import Dict, List
from utils import (get_all_properties_flat, get_connected_properties, 
                   get_shared_properties, jaccard_similarity, cosine_similarity)
from config import WEIGHTS


def cosine_similarity_metric(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> float:
    """
    Similitud coseno vectorizada (bag-of-attributes).
    """
    # Crear vectores de propiedades (frecuencia)
    props_cons = get_connected_properties(subgraph, hotel_consumed)
    props_rec = get_connected_properties(subgraph, hotel_rec)
    
    # Flatten a diccionario de frecuencias
    vec_cons = {}
    for rel_type, values in props_cons.items():
        for val in values:
            key = f"{rel_type}:{val}"
            vec_cons[key] = vec_cons.get(key, 0) + 1
    
    vec_rec = {}
    for rel_type, values in props_rec.items():
        for val in values:
            key = f"{rel_type}:{val}"
            vec_rec[key] = vec_rec.get(key, 0) + 1
    
    return cosine_similarity(vec_cons, vec_rec)

def shared_attribute_count(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> int:
    """
    Conteo absoluto de atributos compartidos.
    SharedCount = |Props(h) ∩ Props(rec)|
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_rec)
    return sum(len(values) for values in shared.values())

def shared_category_count(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> int:
    """
    Número de categorías compartidas (solo has_category).
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_rec)
    return len(shared.get('has_category', []))

def shared_location_count(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> int:
    """
    Cantidad de coincidencias en ubicación (ciudad, estado, postal).
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_rec)
    
    location_types = ['located_in_city', 'in_state', 'has_postal_code']
    count = 0
    for loc_type in location_types:
        count += len(shared.get(loc_type, []))
    
    return count

def category_alignment_score(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Qué tan alineadas están las categorías del recomendado con las del usuario.
    CAS = |Cat(rec) ∩ Cat(user)| / |Cat(rec)|
    """
    from utils import get_all_user_properties
    
    # Categorías del recomendado
    rec_props = get_connected_properties(subgraph, hotel_rec)
    rec_cats = set(rec_props.get('has_category', []))
    
    if not rec_cats:
        return 0.0
    
    # Categorías del usuario
    user_props = get_all_user_properties(subgraph, consumed_hotels)
    user_cats = user_props.get('has_category', set())
    
    intersection = rec_cats & user_cats
    return len(intersection) / len(rec_cats)

def path_count_graph(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> int:
    """
    Número de caminos entre consumido y recomendado.
    Cada atributo compartido = 1 camino
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_rec)
    return sum(len(values) for values in shared.values())

def path_length_graph(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> int:
    """
    Longitud de la ruta más corta.
    En tu grafo: 2 si comparten atributo, inf si no.
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_rec)
    if shared:
        return 2  # hotel -> atributo -> hotel
    return float('inf')

def weighted_knowledge_path_score_similarity(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> float:
    """
    Suma de pesos de los caminos relevantes.
    KPS = Σ weight(path)
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_rec)
    
    kps = 0.0
    for rel_type, values in shared.items():
        weight = WEIGHTS.get(rel_type, 1.0)
        kps += weight * len(values)
    
    return kps

def compute_all_similarity_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                   consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas de similitud.
    
    Returns:
        Lista de dicts con métricas por cada par (hotel_consumido, hotel_recomendado)
    """
    results = []
    
    # Métrica global
    cas = category_alignment_score(subgraph, consumed_hotels, hotel_rec_id)
    
    # Métricas por cada hotel consumido
    for hotel_cons in consumed_hotels:
        cosine = cosine_similarity_metric(subgraph, hotel_cons, hotel_rec_id)
        shared_count = shared_attribute_count(subgraph, hotel_cons, hotel_rec_id)
        shared_cats = shared_category_count(subgraph, hotel_cons, hotel_rec_id)
        shared_locs = shared_location_count(subgraph, hotel_cons, hotel_rec_id)
        pc = path_count_graph(subgraph, hotel_cons, hotel_rec_id)
        pl = path_length_graph(subgraph, hotel_cons, hotel_rec_id)
        kps = weighted_knowledge_path_score_similarity(subgraph, hotel_cons, hotel_rec_id)
        
        result = {
            'usuario': user_id,
            'hotel_recomendado': hotel_rec_id,
            'hotel_consumido': hotel_cons,
            'propiedad': None,
            'cosine_similarity': cosine,
            'shared_attribute_count': shared_count,
            'shared_category_count': shared_cats,
            'shared_location_count': shared_locs,
            'category_alignment_score': cas,
            'path_count': pc,
            'path_length': pl,
            'weighted_kps': kps
        }
        results.append(result)
    
    return results