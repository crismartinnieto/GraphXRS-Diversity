"""
Métricas basadas en cobertura del perfil del usuario
"""
from typing import Dict, List
from utils import get_all_properties_flat, get_all_user_properties

def preference_coverage(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Cobertura de preferencias: proporción de atributos del usuario presentes en el recomendado.
    Coverage = |Props(rec) ∩ Props(cons)| / |Props(cons)|
    """
    rec_props = get_all_properties_flat(subgraph, hotel_rec)
    user_props_dict = get_all_user_properties(subgraph, consumed_hotels)
    user_props = set()
    for values in user_props_dict.values():
        user_props.update(values)
    
    if not user_props:
        return 0.0
    
    intersection = rec_props & user_props
    return len(intersection) / len(user_props)

def blind_spot_coverage(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Blind-Spot Coverage (Tintarev & Masthoff): 
    Cuánta información nueva aporta el recomendado.
    BlindSpot = 1 - Coverage
    """
    coverage = preference_coverage(subgraph, consumed_hotels, hotel_rec)
    return 1.0 - coverage

def compute_all_coverage_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                 consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas de cobertura.
    
    Returns:
        Lista con una sola fila (métricas globales)
    """
    pref_cov = preference_coverage(subgraph, consumed_hotels, hotel_rec_id)
    blind_spot = blind_spot_coverage(subgraph, consumed_hotels, hotel_rec_id)
    
    result = {
        'usuario': user_id,
        'hotel_recomendado': hotel_rec_id,
        'hotel_consumido': None,
        'propiedad': None,
        'preference_coverage': pref_cov,
        'blind_spot_coverage': blind_spot
    }
    
    return [result]