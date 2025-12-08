"""
Métricas basadas en ejemplos (Example-based metrics)
"""
import statistics
from typing import Dict, List, Tuple
from utils import get_all_properties_flat, jaccard_similarity, get_shared_properties
from config import SIMILARITY_CONFIG

def example_similarity_score(subgraph: Dict, hotel_consumed: str, hotel_rec: str) -> float:
    """
    Similitud Jaccard entre un hotel consumido y el recomendado.
    Similarity = |Props_rec ∩ Props_h| / |Props_rec ∪ Props_h|
    """
    props_cons = get_all_properties_flat(subgraph, hotel_consumed)
    props_rec = get_all_properties_flat(subgraph, hotel_rec)
    
    return jaccard_similarity(props_cons, props_rec)

def most_similar_consumed_example(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> Tuple[str, float]:
    """
    Encuentra el hotel consumido más similar al recomendado.
    Returns: (hotel_id, similarity_score)
    """
    if not consumed_hotels:
        return (None, 0.0)
    
    best_hotel = None
    best_sim = -1.0
    
    for hotel_cons in consumed_hotels:
        sim = example_similarity_score(subgraph, hotel_cons, hotel_rec)
        if sim > best_sim:
            best_sim = sim
            best_hotel = hotel_cons
    
    return (best_hotel, best_sim)

def least_similar_consumed_example(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> Tuple[str, float]:
    """
    Encuentra el hotel consumido menos similar (para explicaciones contrastivas).
    Returns: (hotel_id, similarity_score)
    """
    if not consumed_hotels:
        return (None, 0.0)
    
    worst_hotel = None
    worst_sim = float('inf')
    
    for hotel_cons in consumed_hotels:
        sim = example_similarity_score(subgraph, hotel_cons, hotel_rec)
        if sim < worst_sim:
            worst_sim = sim
            worst_hotel = hotel_cons
    
    return (worst_hotel, worst_sim)

def mean_example_similarity(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Promedio de similitud del recomendado con todos los consumidos.
    MeanSim = (1/k) × Σ Similarity(h_i, rec)
    """
    if not consumed_hotels:
        return 0.0
    
    similarities = [example_similarity_score(subgraph, h, hotel_rec) for h in consumed_hotels]
    return statistics.mean(similarities)

def k_nearest_example_strength(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str, k: int = None) -> float:
    """
    Suma de similitudes de los k ejemplos más similares.
    kNES = Σ Similarity(h, rec) for h in top-k
    """
    if k is None:
        k = SIMILARITY_CONFIG['k_nearest']
    
    if not consumed_hotels:
        return 0.0
    
    similarities = [(h, example_similarity_score(subgraph, h, hotel_rec)) for h in consumed_hotels]
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    top_k = similarities[:k]
    return sum(sim for _, sim in top_k)

def example_support_score(subgraph: Dict, consumed_hotels: List[str], 
                         property_type: str, property_value: str) -> int:
    """
    Cuántos consumidos tienen este atributo del recomendado.
    Support(p) = |{h ∈ H_user : p ∈ Props(h)}|
    """
    from utils import get_connected_properties
    
    count = 0
    for hotel_id in consumed_hotels:
        props = get_connected_properties(subgraph, hotel_id)
        if property_value in props.get(property_type, []):
            count += 1
    return count

def example_density(subgraph: Dict, consumed_hotels: List[str], 
                   property_type: str, property_value: str) -> float:
    """
    Frecuencia del atributo dentro de TODOS los atributos consumidos.
    Density(p) = Support(p) / |Props(cons)|
    """
    from utils import get_all_user_properties
    
    user_props = get_all_user_properties(subgraph, consumed_hotels)
    total_props = sum(len(values) for values in user_props.values())
    
    if total_props == 0:
        return 0.0
    
    support = example_support_score(subgraph, consumed_hotels, property_type, property_value)
    return support / total_props

def example_coverage(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Porcentaje de consumidos que comparten al menos un atributo con el recomendado.
    Coverage = #{h: Props(h) ∩ Props(rec) ≠ ∅} / |H_user|
    """
    if not consumed_hotels:
        return 0.0
    
    count = 0
    for hotel_cons in consumed_hotels:
        shared = get_shared_properties(subgraph, hotel_cons, hotel_rec)
        if shared:  # Si hay al menos una propiedad compartida
            count += 1
    
    return count / len(consumed_hotels)

def example_consensus_score(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Homogeneidad: promedio de atributos compartidos por cada ejemplo.
    Consensus = Σ SharedCount(h) / k
    """
    if not consumed_hotels:
        return 0.0
    
    total_shared = 0
    for hotel_cons in consumed_hotels:
        shared = get_shared_properties(subgraph, hotel_cons, hotel_rec)
        shared_count = sum(len(values) for values in shared.values())
        total_shared += shared_count
    
    return total_shared / len(consumed_hotels)

def example_disagreement_score(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> float:
    """
    Variabilidad en la similitud de los ejemplos.
    Disagreement = Var(Similarity(h_i, rec))
    """
    if len(consumed_hotels) < 2:
        return 0.0
    
    similarities = [example_similarity_score(subgraph, h, hotel_rec) for h in consumed_hotels]
    return statistics.variance(similarities)

def prototype_example_score(subgraph: Dict, consumed_hotels: List[str], hotel_rec: str) -> Tuple[str, float]:
    """
    El ejemplo más representativo (más similar al centroide del usuario).
    Aproximación: el que tiene mayor similitud promedio con los demás.
    Returns: (prototype_hotel_id, similarity_to_rec)
    """
    if not consumed_hotels:
        return (None, 0.0)
    
    # Calcular similitud promedio de cada hotel con los demás
    avg_sims = {}
    for h1 in consumed_hotels:
        sims = []
        for h2 in consumed_hotels:
            if h1 != h2:
                sims.append(example_similarity_score(subgraph, h1, h2))
        avg_sims[h1] = statistics.mean(sims) if sims else 0.0
    
    # El prototipo es el de mayor similitud promedio
    prototype = max(avg_sims, key=avg_sims.get)
    
    # Su similitud con el recomendado
    sim_to_rec = example_similarity_score(subgraph, prototype, hotel_rec)
    
    return (prototype, sim_to_rec)

def compute_all_example_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                consumed_hotels: List[str]) -> List[Dict]:
    """
    Calcula todas las métricas basadas en ejemplos para un usuario y un hotel recomendado.
    Ahora INCLUYE Example Density como métrica global agregada.
    """

    from utils import get_hotel_properties
    from metrics_examples import example_density

    results = []
    
    # ----- MÉTRICAS GLOBALES -----
    mean_sim = mean_example_similarity(subgraph, consumed_hotels, hotel_rec_id)
    knes = k_nearest_example_strength(subgraph, consumed_hotels, hotel_rec_id)
    coverage = example_coverage(subgraph, consumed_hotels, hotel_rec_id)
    consensus = example_consensus_score(subgraph, consumed_hotels, hotel_rec_id)
    disagreement = example_disagreement_score(subgraph, consumed_hotels, hotel_rec_id)
    
    # Identificación de ejemplos especiales
    most_sim_hotel, most_sim_score = most_similar_consumed_example(subgraph, consumed_hotels, hotel_rec_id)
    least_sim_hotel, least_sim_score = least_similar_consumed_example(subgraph, consumed_hotels, hotel_rec_id)
    prototype_hotel, prototype_score = prototype_example_score(subgraph, consumed_hotels, hotel_rec_id)

    # ----- NEW: DENSIDAD DEL HOTEL RECOMENDADO -----
    # Promedio de densidad de TODOS los atributos del recomendado
    rec_props = get_hotel_properties(subgraph, hotel_rec_id)  # dict: {prop_type: [values]}
    
    density_values = []
    for p_type, values in rec_props.items():
        for val in values:
            d = example_density(subgraph, consumed_hotels, p_type, val)
            density_values.append(d)

    example_density_global = sum(density_values) / len(density_values) if density_values else 0.0
    
    # ----- MÉTRICAS POR EJEMPLO -----
    for hotel_cons in consumed_hotels:
        sim = example_similarity_score(subgraph, hotel_cons, hotel_rec_id)

        result = {
            'usuario': user_id,
            'hotel_recomendado': hotel_rec_id,
            'hotel_consumido': hotel_cons,
            'propiedad': None,

            # --- MÉTRICAS POR EJEMPLO ---
            'example_similarity_score': sim,

            # --- MÉTRICAS GLOBALES ---
            'mean_example_similarity': mean_sim,
            'k_nearest_example_strength': knes,
            'example_coverage': coverage,
            'example_consensus_score': consensus,
            'example_disagreement_score': disagreement,
            'example_density_global': example_density_global,  

            # --- FLAGS ESPECIALES ---
            'is_most_similar': 1 if hotel_cons == most_sim_hotel else 0,
            'is_least_similar': 1 if hotel_cons == least_sim_hotel else 0,

            # --- SOLO PARA EL PROTOTIPO ---
            'prototype_similarity': prototype_score if hotel_cons == prototype_hotel else 0.0
        }
        results.append(result)
    
    return results
