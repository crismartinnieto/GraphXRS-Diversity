# metrics_paths.py
# Métricas relacionadas con caminos en el subgrafo (path-based). En tu JSON la mayoría serán paths de longitud 2.

import numpy as np
from collections import defaultdict

def path_length_between_businesses(shared_attrs: set):
    # Si comparten atributo, path length conceptualmente 2 (hotel->attr->hotel)
    return 2 if shared_attrs else np.inf

def path_count(shared_attrs: set):
    return len(shared_attrs)

def path_type_variety(shared_attrs: set):
    # shared_attrs contiene keys tipo "reltype|||name"
    types = set()
    for s in shared_attrs:
        if "|||" in s:
            t, _ = s.split("|||",1)
            types.add(t)
    return len(types), types

def path_type_frequency(shared_attrs: set):
    freq = defaultdict(int)
    for s in shared_attrs:
        if "|||" in s:
            t, _ = s.split("|||",1)
            freq[t] += 1
    return dict(freq)

def path_confidence_score(shared_attrs: set, weights_by_type: dict):
    total = 0.0
    for s in shared_attrs:
        if "|||" in s:
            t, _ = s.split("|||",1)
            total += weights_by_type.get(t, 1.0)
    return total
