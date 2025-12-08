"""
Métricas basadas en diversidad
"""
from typing import Dict, List
from utils import get_connected_properties, get_shared_properties

def explanation_type_diversity(subgraph: Dict, hotel_consumed: str, hotel_recommended: str) -> int:
    """
    Diversidad de tipos de relaciones que explican la conexión.
    Diversity = |{tipo_de_relación_que_explica}|
    """
    shared = get_shared_properties(subgraph, hotel_consumed, hotel_recommended)
    return len(shared.keys())

def attribute_diversity_recommended(subgraph: Dict, hotel_rec: str) -> int:
    """
    Diversidad de tipos de atributos en el hotel recomendado.
    Diversity(rec) = |{tipo_de_atributo_en_rec}|
    """
    rec_props = get_connected_properties(subgraph, hotel_rec)
    return len(rec_props.keys())

def cross_explanation_diversity(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Variedad de explicaciones generadas para un usuario.
    Promedio de tipos de relaciones compartidas entre consumidos y recomendado.
    """
    if not consumed_hotels:
        return 0.0
    
    total_diversity = 0
    for hotel_cons in consumed_hotels:
        diversity = explanation_type_diversity(subgraph, hotel_cons, hotel_rec)
        total_diversity += diversity
    
    return total_diversity / len(consumed_hotels)

def compute_all_diversity_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                  consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas de diversidad.
    
    Returns:
        Lista de dicts con métricas por hotel consumido o global
    """
    results = []
    
    # Métrica global del recomendado
    attr_div_rec = attribute_diversity_recommended(subgraph, hotel_rec_id)
    cross_div = cross_explanation_diversity(subgraph, consumed_hotels, hotel_rec_id)
    
    # Métrica por cada hotel consumido
    for hotel_cons in consumed_hotels:
        exp_type_div = explanation_type_diversity(subgraph, hotel_cons, hotel_rec_id)
        
        result = {
            'usuario': user_id,
            'hotel_recomendado': hotel_rec_id,
            'hotel_consumido': hotel_cons,
            'propiedad': None,
            'explanation_type_diversity': exp_type_div,
            'attribute_diversity_recommended': attr_div_rec,
            'cross_explanation_diversity': cross_div
        }
        results.append(result)
    
    return results