"""
Wrapper helper para convertir node_ids a business_ids en los resultados de métricas
"""
from typing import List, Dict
from utils import get_business_property_id

def convert_results_to_business_ids(subgraph: Dict, results: List[Dict], 
                                    hotel_rec_business_id: str,
                                    consumed_node_to_business_map: Dict[str, str]) -> List[Dict]:
    """
    Convierte los IDs de node internos a IDs de negocio en los resultados.
    
    Args:
        subgraph: El subgrafo completo
        results: Lista de dicts con resultados de métricas
        hotel_rec_business_id: ID del negocio recomendado
        consumed_node_to_business_map: Mapeo de node_id -> business_id para consumidos
        
    Returns:
        Lista de dicts con IDs de negocio en lugar de node_ids
    """
    converted_results = []
    
    for result in results:
        new_result = result.copy()
        
        # Convertir hotel_recomendado
        if 'hotel_recomendado' in new_result:
            new_result['hotel_recomendado'] = hotel_rec_business_id
        
        # Convertir hotel_consumido si existe y no es None
        if 'hotel_consumido' in new_result and new_result['hotel_consumido'] is not None:
            node_id = new_result['hotel_consumido']
            new_result['hotel_consumido'] = consumed_node_to_business_map.get(node_id, node_id)
        
        converted_results.append(new_result)
    
    return converted_results

def create_consumed_mapping(subgraph: Dict, consumed_hotels_node_ids: List[str]) -> Dict[str, str]:
    """
    Crea un mapeo de node_id -> business_id para los hoteles consumidos.
    
    Args:
        subgraph: El subgrafo completo
        consumed_hotels_node_ids: Lista de node_ids internos de hoteles consumidos
        
    Returns:
        Dict mapeando node_id -> business_id
    """
    mapping = {}
    for node_id in consumed_hotels_node_ids:
        business_id = get_business_property_id(subgraph, node_id)
        if business_id:
            mapping[node_id] = business_id
    return mapping