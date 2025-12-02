# metrics_centrality.py
# Calcula medidas de centralidad sobre el bipartito Business-Attribute que construiremos en runner.

import networkx as nx
import numpy as np

def degree_centrality_raw(B_global, attr_key):
    node = f"ATTR_{attr_key}"
    return B_global.degree(node) if node in B_global else 0

def degree_centrality_normalized(B_global, attr_key):
    node = f"ATTR_{attr_key}"
    if node not in B_global:
        return 0.0
    N = len([n for n in B_global.nodes() if isinstance(n, str) and n.startswith("BUS_")])
    return B_global.degree(node) / max(1, N-1)

def pagerank_attr(pagerank_dict, attr_key):
    return pagerank_dict.get(f"ATTR_{attr_key}", 0.0)

def eigenvector_attr(eigen_dict, attr_key):
    return eigen_dict.get(f"ATTR_{attr_key}", 0.0)

def betweenness_attr(bet_dict, attr_key):
    return bet_dict.get(f"ATTR_{attr_key}", 0.0)

def harmonic_centrality(B_global, attr_key):
    node = f"ATTR_{attr_key}"
    if node not in B_global:
        return 0.0
    # harmonic centrality as sum(1/dist)
    lengths = nx.single_source_shortest_path_length(B_global, node)
    s = 0.0
    for n, d in lengths.items():
        if d>0:
            s += 1.0/d
    return s

def clustering_coefficient_on_projection(B_global, attr_key):
    # proyectar atributos: construir proyección de atributos vía negocios comunes
    try:
        attrs = [n for n in B_global.nodes() if isinstance(n, str) and n.startswith("ATTR_")]
        # proyect attributes via bipartite projection
        A = nx.bipartite.weighted_projected_graph(B_global, [n for n in B_global.nodes() if n.startswith("BUS_")])
        node = f"ATTR_{attr_key}"
        if node not in A:
            return 0.0
        return nx.clustering(A, node)
    except Exception:
        return 0.0

def attribute_influence_score(degree, amf):
    return degree * amf
