"""
Métricas basadas en centralidad de nodos en el grafo
"""
import networkx as nx
from typing import Dict, List
from utils import build_networkx_graph, get_connected_properties
from config import CENTRALITY_CONFIG

def compute_degree_centrality(G: nx.Graph) -> Dict[str, float]:
    """Degree centrality: cuántos nodos están conectados a cada nodo"""
    return dict(G.degree())

def compute_normalized_degree_centrality(G: nx.Graph) -> Dict[str, float]:
    """Degree centrality normalizado por (N-1)"""
    return nx.degree_centrality(G)

def compute_betweenness_centrality(G: nx.Graph) -> Dict[str, float]:
    """Betweenness centrality: nodos que actúan como puentes"""
    return nx.betweenness_centrality(G, normalized=CENTRALITY_CONFIG['betweenness_normalized'])

def compute_closeness_centrality(G: nx.Graph) -> Dict[str, float]:
    """Closeness centrality: qué tan cerca está un nodo de todos los demás"""
    return nx.closeness_centrality(G)

def compute_eigenvector_centrality(G: nx.Graph) -> Dict[str, float]:
    """Eigenvector centrality: qué tan conectado está con nodos importantes"""
    try:
        return nx.eigenvector_centrality(G, max_iter=1000)
    except:
        # Si el grafo no converge, retorna zeros
        return {node: 0.0 for node in G.nodes()}

def compute_pagerank(G: nx.Graph) -> Dict[str, float]:
    """PageRank: métrica muy popular en graph-XAI"""
    return nx.pagerank(G, alpha=CENTRALITY_CONFIG['pagerank_alpha'])

def compute_harmonic_centrality(G: nx.Graph) -> Dict[str, float]:
    """Harmonic centrality: suma de inversos de distancias"""
    return nx.harmonic_centrality(G)

def compute_attribute_influence_score(G: nx.Graph, amf_scores: Dict[str, float]) -> Dict[str, float]:
    """
    Attribute Influence = Degree(p) × AMF(p)
    Combina centralidad con frecuencia de match del atributo
    
    Args:
        amf_scores: Dict con AMF pre-calculado para cada propiedad
    """
    degree = compute_degree_centrality(G)
    
    influence = {}
    for node, deg in degree.items():
        influence[node] = deg * amf_scores.get(node, 0.0)
    
    return influence

def compute_all_centrality_metrics(subgraph: Dict, user_id: int, hotel_rec_id: str, 
                                   consumed_hotels: List[str], amf_scores: Dict[str, float] = None) -> List[Dict]:
    """
    Calcula todas las métricas de centralidad para cada propiedad del grafo.
    
    Returns:
        Lista de dicts con métricas de centralidad por cada propiedad/nodo
    """
    G = build_networkx_graph(subgraph)
    
    # Calcular todas las centralidades
    degree_cent = compute_degree_centrality(G)
    norm_degree_cent = compute_normalized_degree_centrality(G)
    betweenness_cent = compute_betweenness_centrality(G)
    closeness_cent = compute_closeness_centrality(G)
    eigenvector_cent = compute_eigenvector_centrality(G)
    pagerank_cent = compute_pagerank(G)
    harmonic_cent = compute_harmonic_centrality(G)
    
    # Attribute influence (requiere AMF pre-calculado)
    if amf_scores is None:
        amf_scores = {}
    influence_score = compute_attribute_influence_score(G, amf_scores)
    
    results = []
    
    # Obtener propiedades del hotel recomendado
    rec_props = get_connected_properties(subgraph, hotel_rec_id)
    
    # Iterar sobre cada propiedad del hotel recomendado
    for rel_type, values in rec_props.items():
        for prop_value in values:
            # Buscar el node_id que representa esta propiedad
            prop_node_id = None
            for node in subgraph['nodes']:
                if node.get('properties', {}).get('name') == prop_value:
                    prop_node_id = node['id']
                    break
            
            if prop_node_id and prop_node_id in G.nodes():
                result = {
                    'usuario': user_id,
                    'hotel_recomendado': hotel_rec_id,
                    'propiedad': f"{rel_type}:{prop_value}",
                    'hotel_consumido': None,  # Métricas de centralidad son globales
                    'degree_centrality': degree_cent.get(prop_node_id, 0),
                    'normalized_degree_centrality': norm_degree_cent.get(prop_node_id, 0.0),
                    'betweenness_centrality': betweenness_cent.get(prop_node_id, 0.0),
                    'closeness_centrality': closeness_cent.get(prop_node_id, 0.0),
                    'eigenvector_centrality': eigenvector_cent.get(prop_node_id, 0.0),
                    'pagerank': pagerank_cent.get(prop_node_id, 0.0),
                    'harmonic_centrality': harmonic_cent.get(prop_node_id, 0.0),
                    'attribute_influence_score': influence_score.get(prop_node_id, 0.0)
                }
                results.append(result)
    
    return results