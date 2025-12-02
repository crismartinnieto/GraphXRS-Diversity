# metrics_similarity.py
import numpy as np
from collections import Counter

def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0

def cosine_similarity_from_vectors(vec_a, vec_b) -> float:
    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

def best_worst_mean_similarity(rec_attrs: set, consumed_attr_sets: dict):
    sims = []
    for _, attrs in consumed_attr_sets.items():
        sims.append(jaccard_similarity(rec_attrs, attrs))
    if not sims:
        return 0.0, 0.0, 0.0
    return max(sims), min(sims), float(sum(sims)/len(sims))

def k_nearest_example_strength(rec_attrs: set, consumed_attr_sets: dict, k=3):
    sims = []
    for _, attrs in consumed_attr_sets.items():
        sims.append(jaccard_similarity(rec_attrs, attrs))
    sims_sorted = sorted(sims, reverse=True)[:k]
    return float(sum(sims_sorted)) if sims_sorted else 0.0

def prototype_similarity(consumed_attr_sets: dict, rec_attrs: set):
    # prototype = elemento más cercano al centroide binario (argmin dist to mean vector)
    # Para simplicidad: elegir el consumido con mayor suma de intersecciones con los demás (grado de representatividad)
    if not consumed_attr_sets:
        return 0.0, None
    nodes = list(consumed_attr_sets.keys())
    best_node = None
    best_score = -1
    for n in nodes:
        score = 0
        for m in nodes:
            if m == n: continue
            score += len(consumed_attr_sets[n] & consumed_attr_sets[m])
        if score > best_score:
            best_score = score
            best_node = n
    proto_sim = jaccard_similarity(consumed_attr_sets[best_node], rec_attrs) if best_node else 0.0
    return proto_sim, best_node

def example_consensus_score(consumed_attr_sets: dict, rec_attrs: set):
    # Qué tan homogéneos son los ejemplos que apoyan rec_attrs: usar Varianza de similitudes
    sims = [jaccard_similarity(rec_attrs, s) for s in consumed_attr_sets.values()]
    if not sims:
        return 0.0, 0.0
    import numpy as np
    return float(np.mean(sims)), float(np.var(sims))
