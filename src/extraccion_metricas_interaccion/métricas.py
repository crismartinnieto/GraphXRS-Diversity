"""
src/extraccion_metricas_interaccion/metricas.py

Métricas XAI sobre el grafo de interacción (CF).

Constantes exportadas:
    NOMBRES_METRICAS_CF  — lista de nombres de métricas, usada por pipeline.py

Función pública principal:
    calcular_metricas_cf(json_path, user_id, hotel_rec)
    → lista de dicts, una fila por hotel_explicador (compartido)
"""
import json
import networkx as nx
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


# ============================================================
# ÍNDICE DEL SUBGRAFO
# ============================================================

def _build_index(nodes: list, relationships: list) -> dict:
    degree_count    = defaultdict(int)
    node_info       = {}
    rels_por_inicio = defaultdict(dict)
    rels_por_fin    = defaultdict(dict)

    for node in nodes:
        nid = node['id']
        node_info[nid] = {
            'degree':     0,
            'labels':     node.get('labels', []),
            'properties': node.get('properties', {})
        }

    adjacency = defaultdict(set)
    for rel in relationships:
        s = rel['start_node_id']
        e = rel['end_node_id']
        adjacency[s].add(e)
        adjacency[e].add(s)

    for nid in node_info:
        degree_count[nid] = len(adjacency[nid])

    for nid, cnt in degree_count.items():
        if nid in node_info:
            node_info[nid]['degree'] = cnt

    usuario_objetivo     = None
    hotel_recomendado    = None
    usuarios_intermedios = {}
    hoteles_compartidos  = {}

    for nid, info in node_info.items():
        tipo = info['properties'].get('type', '')
        if 'User' in info['labels']:
            if tipo == 'objetivo':
                usuario_objetivo = (nid, info)
            elif tipo == 'intermedio':
                usuarios_intermedios[nid] = info
        elif 'Business' in info['labels']:
            if tipo == 'recomendado':
                hotel_recomendado = (nid, info)
            elif tipo == 'compartido':
                hoteles_compartidos[nid] = info

    return {
        'node_info':            node_info,
        'rels_por_inicio':      dict(rels_por_inicio),
        'rels_por_fin':         dict(rels_por_fin),
        'usuario_objetivo':     usuario_objetivo,
        'hotel_recomendado':    hotel_recomendado,
        'usuarios_intermedios': usuarios_intermedios,
        'hoteles_compartidos':  hoteles_compartidos,
    }


# ============================================================
# ESTRATEGIAS
# ============================================================

class MetricaCFStrategy(ABC):
    @abstractmethod
    def calcular(self, node_id: str, node_info: dict, index: dict) -> float:
        pass
    @abstractmethod
    def nombre(self) -> str:
        pass


class DegreeCentralidadHotelStrategy(MetricaCFStrategy):
    def calcular(self, node_id, node_info, index):
        return float(node_info['degree'])
    def nombre(self): return 'cf_degree_hotel'


class RatioUsuariosCompartidosStrategy(MetricaCFStrategy):
    def calcular(self, node_id, node_info, index):
        usuarios_intermedios = index['usuarios_intermedios']
        if not usuarios_intermedios:
            return 0.0
        n = sum(1 for uid in index['rels_por_fin'].get(node_id, {})
                if uid in usuarios_intermedios)
        return n / len(usuarios_intermedios)
    def nombre(self): return 'cf_ratio_usuarios_compartidos'


class NormDegreeCentralidadHotelStrategy(MetricaCFStrategy):
    def calcular(self, node_id, node_info, index):
        n = len(index['node_info'])
        return float(node_info['degree']) / (n - 1) if n > 1 else 0.0
    def nombre(self): return 'cf_norm_degree_hotel'

class BetweennessHotelStrategy(MetricaCFStrategy):
    """
    Betweenness centrality dirigida del hotel compartido en el subgrafo CF.
    Se construye un DiGraph con networkx usando todos los nodos y relaciones
    del subgrafo, se calcula betweenness normalizada sobre el grafo completo,
    y se devuelve solo el score del hotel compartido (nodo Business).

    Interpretación: valor alto → el hotel es un puente obligado en muchos
    caminos mínimos del subgrafo, lo que refuerza su rol explicador.
    """
    def _build_digraph(self, index: dict) -> nx.DiGraph:
        G = nx.Graph()
        for nid in index['node_info']:
            G.add_node(nid)
        for start, ends in index['rels_por_inicio'].items():
            for end in ends:
                G.add_edge(start, end)
        return G

    def calcular(self, node_id, node_info, index):
        G = self._build_digraph(index)
        betweenness = nx.betweenness_centrality(G, normalized=True)
        return betweenness.get(node_id, 0.0)

    def nombre(self): return 'cf_betweenness_hotel'


# ============================================================
# INSTANCIAS Y CONSTANTE EXPORTADA
# ============================================================

ESTRATEGIAS_CF      = [
    DegreeCentralidadHotelStrategy(),
    RatioUsuariosCompartidosStrategy(),
    NormDegreeCentralidadHotelStrategy(),
    BetweennessHotelStrategy(),
]
NOMBRES_METRICAS_CF = [e.nombre() for e in ESTRATEGIAS_CF]


# ============================================================
# FUNCIÓN PÚBLICA PRINCIPAL
# ============================================================

def calcular_metricas_cf(
    json_path: Path,
    user_id: int,
    hotel_rec: int
) -> List[Dict[str, Any]]:
    """
    Calcula todas las métricas CF para un par (user, hotel_rec).
    Devuelve lista de dicts, una fila por hotel compartido (explicador).
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    index = _build_index(data.get('nodes', []), data.get('relationships', []))

    if index['usuario_objetivo'] is None:
        print(f"  [CF] Sin usuario objetivo en subgrafo user={user_id}")
        return []

    rels_por_fin    = index['rels_por_fin']
    usuarios_interm = index['usuarios_intermedios']
    filas           = []

    for h_id, h_info in index['hoteles_compartidos'].items():
        n_valoraron = sum(
            1 for uid in rels_por_fin.get(h_id, {})
            if uid in usuarios_interm
        )
        if h_info['degree'] == 0 or n_valoraron == 0:
            continue

        hotel_real_id = h_info['properties'].get('id', h_id)
        fila          = {'hotel_explicador': hotel_real_id}

        for estrategia in ESTRATEGIAS_CF:
            try:
                fila[estrategia.nombre()] = estrategia.calcular(h_id, h_info, index)
            except Exception as e:
                print(f"  [CF] Error en {estrategia.nombre()}: {e}")
                fila[estrategia.nombre()] = None

        filas.append(fila)

    # Filtrar filas donde TODAS las métricas son 0 o None
    filas = [
        fila for fila in filas
        if any(
            fila.get(e.nombre()) not in (0, 0.0, None)
            for e in ESTRATEGIAS_CF
        )
    ]

    return filas