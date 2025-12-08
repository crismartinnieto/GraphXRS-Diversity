"""
Métricas basadas en caminos (Path-based metrics)
"""
import networkx as nx
from typing import Dict, List
from utils import get_shared_properties, build_networkx_graph
from config import WEIGHTS, RELATION_TYPES

def path_length(subgraph: Dict, hotel_consumed: str, hotel_recommended: str) -> int:
    """
    Longitud del camino más corto entre hotel consumido y recomendado.
    En tu grafo: hotel -> atributo -> hotel = longitud 2 si comparten atributo
    """
    G = build_networkx_graph(subgraph)
    
    try:
        length = nx.shortest_path_length(G, hotel_consumed, hotel_recommended)
        return length
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return float('inf')  # No hay camino

def path_count(subgraph: Dict, hotel_consumed: str, hotel_recommended: str) -> int:
    """
    Número de caminos distintos entre dos hoteles.
    Cada atributo compartido = 1 camino
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_recommended)
    
    # Contar total de propiedades compartidas (cada una es un camino)
    total_paths = sum(len(values) for values in shared.values())
    return total_paths

def shared_property_weight_score(subgraph: Dict, hotel_consumed: str, hotel_recommended: str) -> float:
    """
    Suma de pesos de propiedades compartidas según su importancia.
    Score = Σ w(p) para cada propiedad compartida
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_recommended)
    
    score = 0.0
    for rel_type, values in shared.items():
        weight = WEIGHTS.get(rel_type, 1.0)
        score += weight * len(values)
    
    return score

def path_type_variety(subgraph: Dict, hotel_consumed: str, hotel_recommended: str) -> int:
    """
    Número de tipos de relación distintos compartidos.
    Ejemplo: si comparten 'has_category', 'located_in_city' -> variety = 2
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_recommended)
    return len(shared.keys())

def path_type_frequency(subgraph: Dict, consumed_hotels: List[str], hotel_recommended: str) -> Dict[str, int]:
    """
    Para cada tipo de relación t, cuenta cuántos hoteles consumidos 
    comparten ese tipo con el recomendado.
    
    Returns:
        Dict: {'has_category': 3, 'located_in_city': 2, ...}
    """
    frequency = {}
    
    for hotel_cons in consumed_hotels:
        shared = get_shared_properties(subgraph, hotel_cons, hotel_recommended)
        for rel_type in shared.keys():
            frequency[rel_type] = frequency.get(rel_type, 0) + 1
    
    return frequency

def path_confidence_score(subgraph: Dict, hotel_consumed: str, hotel_recommended: str) -> float:
    """
    Suma de pesos de tipos de relación compartidos.
    Confidence = Σ w(t) para cada tipo t compartido
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_recommended)
    
    score = 0.0
    for rel_type in shared.keys():
        score += WEIGHTS.get(rel_type, 1.0)
    
    return score

def weighted_knowledge_path_score(subgraph: Dict, hotel_consumed: str, hotel_recommended: str) -> float:
    """
    Suma de pesos de todos los caminos relevantes.
    KPS = Σ weight(path) considerando tanto tipo como cantidad
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_recommended)
    
    kps = 0.0
    for rel_type, values in shared.items():
        weight = WEIGHTS.get(rel_type, 1.0)
        # Cada valor compartido contribuye con el peso del tipo
        kps += weight * len(values)
    
    return kps

def compute_all_path_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas de caminos para cada par (hotel_consumido, hotel_recomendado).
    
    Returns:
        Lista de dicts con métricas por cada hotel consumido
    """
    results = []
    
    # Métricas globales (frecuencia de tipos)
    type_freq = path_type_frequency(subgraph, consumed_hotels, hotel_rec_id)
    
    for hotel_cons in consumed_hotels:
        shared = get_shared_properties(subgraph, hotel_cons, hotel_rec_id)
        
        # Si no comparten nada, algunas métricas serán 0
        if not shared:
            result = {
                'usuario': user_id,
                'hotel_recomendado': hotel_rec_id,
                'hotel_consumido': hotel_cons,
                'propiedad': None,
                'path_length': float('inf'),
                'path_count': 0,
                'path_type_variety': 0,
                'shared_property_weight_score': 0.0,
                'path_confidence_score': 0.0,
                'weighted_kps': 0.0
            }
            results.append(result)
        else:
            # Métricas agregadas por hotel
            pl = path_length(subgraph, hotel_cons, hotel_rec_id)
            pc = path_count(subgraph, hotel_cons, hotel_rec_id)
            ptv = path_type_variety(subgraph, hotel_cons, hotel_rec_id)
            spws = shared_property_weight_score(subgraph, hotel_cons, hotel_rec_id)
            pcs = path_confidence_score(subgraph, hotel_cons, hotel_rec_id)
            kps = weighted_knowledge_path_score(subgraph, hotel_cons, hotel_rec_id)
            
            # Generar una fila por cada propiedad compartida
            for rel_type, values in shared.items():
                for prop_value in values:
                    result = {
                        'usuario': user_id,
                        'hotel_recomendado': hotel_rec_id,
                        'hotel_consumido': hotel_cons,
                        'propiedad': f"{rel_type}:{prop_value}",
                        'path_length': pl,
                        'path_count': pc,
                        'path_type_variety': ptv,
                        'shared_property_weight_score': spws,
                        'path_confidence_score': pcs,
                        'weighted_kps': kps,
                        'path_type_frequency': type_freq.get(rel_type, 0)
                    }
                    results.append(result)
    
    return results