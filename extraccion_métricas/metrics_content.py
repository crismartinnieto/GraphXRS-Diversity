# metrics_content.py
# Métricas de atributo / contenido

from collections import Counter
from math import log
import numpy as np

def attribute_match_frequency(prop_key: str, consumed_nodes: list, business_attributes: dict) -> float:
    """AMF: proporción de hoteles consumidos que tienen prop_key"""
    if not consumed_nodes:
        return 0.0
    support = sum(1 for n in consumed_nodes if prop_key in business_attributes.get(n, set()))
    return support / len(consumed_nodes)

def attribute_presence_ratio(rec_attrs: set, consumed_union: set) -> float:
    """APR = qué fracción de atributos del recomendado aparecen en consumidos"""
    if not rec_attrs:
        return 0.0
    return len(rec_attrs & consumed_union) / len(rec_attrs)

def attribute_tf_user(prop_key: str, consumed_nodes: list, business_attributes: dict) -> int:
    return sum(1 for n in consumed_nodes if prop_key in business_attributes.get(n, set()))

def compute_idf(df_counts: dict, N: int) -> dict:
    idf = {}
    for k, df in df_counts.items():
        idf[k] = log((N + 1) / (df + 1)) + 1.0
    return idf

def tf_idf_user(tf_user: int, idf_value: float) -> float:
    return tf_user * (idf_value if idf_value is not None else 0.0)

def attribute_novelty(prop_key: str, tf_user_val: int) -> int:
    return 1 if tf_user_val == 0 else 0

def attribute_specificity(popularity_degree: int) -> float:
    return 1.0 / (popularity_degree if popularity_degree and popularity_degree>0 else 1.0)

def attribute_overlap_count(rec_attrs: set, consumed_attrs: set) -> int:
    return len(rec_attrs & consumed_attrs)

def attribute_overlap_ratio(rec_attrs: set, consumed_attrs: set) -> float:
    union = rec_attrs | consumed_attrs
    if not union:
        return 0.0
    return len(rec_attrs & consumed_attrs) / len(union)

def novelty_count(rec_attrs: set, consumed_union: set) -> int:
    return len(rec_attrs - consumed_union)

def novelty_ratio(rec_attrs: set, consumed_union: set) -> float:
    if not rec_attrs:
        return 0.0
    return len(rec_attrs - consumed_union) / len(rec_attrs)
