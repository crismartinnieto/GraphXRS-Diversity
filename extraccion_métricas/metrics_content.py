"""
Métricas basadas en contenido/atributos
"""
import math
from typing import Dict, List, Set
from utils import (get_connected_properties, get_all_properties_flat, 
                   get_all_user_properties, get_business_nodes)
from collections import Counter

def attribute_match_frequency(subgraph: Dict, consumed_hotels: List[str], 
                              property_type: str, property_value: str) -> float:
    """
    AMF: Proporción de hoteles consumidos que tienen este atributo.
    AMF(p) = |H_user ∩ {h: p ∈ h}| / |H_user|
    """
    if not consumed_hotels:
        return 0.0
    
    count = 0
    for hotel_id in consumed_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        if property_value in props.get(property_type, []):
            count += 1
    
    return count / len(consumed_hotels)

def attribute_frequency(subgraph: Dict, consumed_hotels: List[str], 
                       property_type: str, property_value: str) -> int:
    """
    TF: Frecuencia absoluta del atributo en los consumidos.
    TF(p) = |{h_user: p ∈ h}|
    """
    count = 0
    for hotel_id in consumed_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        if property_value in props.get(property_type, []):
            count += 1
    return count

def attribute_tfidf(subgraph: Dict, consumed_hotels: List[str], 
                   property_type: str, property_value: str) -> float:
    """
    TF-IDF: TF(p) × log(N / df(p))
    Destaca atributos frecuentes en el usuario pero raros en el catálogo.
    """
    # TF en consumidos
    tf = attribute_frequency(subgraph, consumed_hotels, property_type, property_value)
    
    # DF en todo el catálogo (todos los Business del grafo)
    all_hotels = get_business_nodes(subgraph)
    df = 0
    for hotel_id in all_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        if property_value in props.get(property_type, []):
            df += 1
    
    # TF-IDF
    N = len(all_hotels)
    if df == 0 or N == 0:
        return 0.0
    
    idf = math.log(N / df)
    return tf * idf

def attribute_contribution_score(subgraph: Dict, consumed_hotels: List[str], 
                                 hotel_rec_id: str, property_type: str, property_value: str) -> float:
    """
    Contribution = freq_user(p) × relevance_item(p)
    relevance_item = 1 si el recomendado tiene p, 0 si no
    """
    # Frecuencia en consumidos
    freq_user = attribute_frequency(subgraph, consumed_hotels, property_type, property_value)
    
    # Relevancia en recomendado
    rec_props = get_connected_properties(subgraph, hotel_rec_id)
    relevance_item = 1 if property_value in rec_props.get(property_type, []) else 0
    
    return freq_user * relevance_item

def attribute_overlap_count(subgraph: Dict, consumed_hotels: List[str], hotel_rec_id: str) -> int:
    """
    Número absoluto de atributos compartidos entre recomendado y consumidos.
    """
    rec_props_flat = get_all_properties_flat(subgraph, hotel_rec_id)
    user_props_dict = get_all_user_properties(subgraph, consumed_hotels)
    user_props_flat = set()
    for values in user_props_dict.values():
        user_props_flat.update(values)
    
    intersection = rec_props_flat & user_props_flat
    return len(intersection)

def attribute_overlap_ratio(subgraph: Dict, consumed_hotels: List[str], hotel_rec_id: str) -> float:
    """
    Jaccard entre atributos del usuario y del recomendado.
    OverlapRatio = |Props(rec) ∩ Props(user)| / |Props(rec) ∪ Props(user)|
    """
    rec_props_flat = get_all_properties_flat(subgraph, hotel_rec_id)
    user_props_dict = get_all_user_properties(subgraph, consumed_hotels)
    user_props_flat = set()
    for values in user_props_dict.values():
        user_props_flat.update(values)
    
    intersection = rec_props_flat & user_props_flat
    union = rec_props_flat | user_props_flat
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)

def attribute_novelty(subgraph: Dict, consumed_hotels: List[str], 
                     property_type: str, property_value: str) -> int:
    """
    Novelty = 1 si el atributo NO está en Props(user), 0 si sí está.
    """
    user_props_dict = get_all_user_properties(subgraph, consumed_hotels)
    user_props_flat = set()
    for values in user_props_dict.values():
        user_props_flat.update(values)
    
    return 0 if property_value in user_props_flat else 1

def attribute_specificity(subgraph: Dict, property_type: str, property_value: str) -> float:
    """
    Specificity = 1 / popularity(p)
    Cuanto menos popular, más específico/explicativo.
    """
    # Contar en cuántos hoteles aparece
    all_hotels = get_business_nodes(subgraph)
    popularity = 0
    for hotel_id in all_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        if property_value in props.get(property_type, []):
            popularity += 1
    
    if popularity == 0:
        return 0.0
    
    return 1.0 / popularity

def compute_all_content_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas de contenido/atributos.
    
    Returns:
        Lista de dicts con métricas por cada propiedad del hotel recomendado
    """
    results = []
    
    # Métricas globales
    aoc = attribute_overlap_count(subgraph, consumed_hotels, hotel_rec_id)
    aor = attribute_overlap_ratio(subgraph, consumed_hotels, hotel_rec_id)
    
    # Iterar sobre propiedades del recomendado
    rec_props = get_connected_properties(subgraph, hotel_rec_id)
    
    for rel_type, values in rec_props.items():
        for prop_value in values:
            amf = attribute_match_frequency(subgraph, consumed_hotels, rel_type, prop_value)
            af = attribute_frequency(subgraph, consumed_hotels, rel_type, prop_value)
            tfidf = attribute_tfidf(subgraph, consumed_hotels, rel_type, prop_value)
            contrib = attribute_contribution_score(subgraph, consumed_hotels, hotel_rec_id, rel_type, prop_value)
            novelty = attribute_novelty(subgraph, consumed_hotels, rel_type, prop_value)
            specificity = attribute_specificity(subgraph, rel_type, prop_value)


            result = {
                'usuario': user_id,
                'hotel_recomendado': hotel_rec_id,
                'propiedad': f"{rel_type}:{prop_value}",
                'hotel_consumido': None,
                'amf': amf,
                'attribute_frequency': af,
                'attribute_tfidf': tfidf,
                'attribute_contribution_score': contrib,
                'attribute_overlap_count': aoc,
                'attribute_overlap_ratio': aor,
                'attribute_novelty': novelty,
                'attribute_specificity': specificity,
            }
            results.append(result)
    
    return results