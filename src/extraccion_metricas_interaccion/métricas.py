"""
src/extraccion_metricas_interaccion/metricas.py

Métricas XAI sobre el grafo de interacción (CF).
Opera directamente sobre el subgrafo JSON temporal.
Solo considera relaciones con rating real (IS NOT NULL),
ya filtradas desde utils_interaction_patterns.py.

Función pública principal:
    calcular_metricas_cf(json_path, user_id, hotel_rec)
    → lista de dicts con métricas CF por hotel compartido (explicador)
"""
import json
from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional


# ============================================================
# ÍNDICE DEL SUBGRAFO
# ============================================================

def _build_index(nodes: list, relationships: list) -> dict:
    """
    Construye índices rápidos del subgrafo CF.
    Devuelve dict con:
      - node_info: {node_id: {degree, labels, properties}}
      - rels_por_fin: {node_id: {vecino_id: rating}}
      - usuario_objetivo: (node_id, info) | None
      - hotel_recomendado: (node_id, info) | None
      - usuarios_intermedios: {node_id: info}
      - hoteles_compartidos: {node_id: info}
    """
    degree_count     = defaultdict(int)
    node_info        = {}
    rels_por_inicio  = defaultdict(dict)
    rels_por_fin     = defaultdict(dict)

    for node in nodes:
        nid = node['id']
        node_info[nid] = {
            'degree':     0,
            'labels':     node.get('labels', []),
            'properties': node.get('properties', {})
        }

    for rel in relationships:
        s      = rel['start_node_id']
        e      = rel['end_node_id']
        rating = rel.get('properties', {}).get('rating')
        degree_count[s] += 1
        degree_count[e] += 1
        rels_por_inicio[s][e] = rating
        rels_por_fin[e][s]    = rating

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
# ESTRATEGIAS CF (patrón Strategy)
# ============================================================

class MetricaCFStrategy(ABC):
    @abstractmethod
    def calcular(self, node_id: str, node_info: dict, index: dict) -> float:
        pass

    @abstractmethod
    def nombre(self) -> str:
        pass


class DegreeCentralidadHotelStrategy(MetricaCFStrategy):
    """Degree bruto del hotel compartido en el subgrafo."""
    def calcular(self, node_id, node_info, index):
        return float(node_info['degree'])
    def nombre(self): return 'cf_degree_hotel'


class RatioUsuariosCompartidosStrategy(MetricaCFStrategy):
    """Fracción de usuarios intermedios que valoraron este hotel. Rango [0,1]."""
    def calcular(self, node_id, node_info, index):
        usuarios_intermedios = index['usuarios_intermedios']
        if not usuarios_intermedios:
            return 0.0
        rels_por_fin = index['rels_por_fin']
        n_valoraron  = sum(
            1 for uid in rels_por_fin.get(node_id, {})
            if uid in usuarios_intermedios
        )
        return n_valoraron / len(usuarios_intermedios)
    def nombre(self): return 'cf_ratio_usuarios_compartidos'


class NormDegreeCentralidadHotelStrategy(MetricaCFStrategy):
    """Degree normalizado por (nodos del subgrafo - 1). Comparable entre subgrafos."""
    def calcular(self, node_id, node_info, index):
        n = len(index['node_info'])
        return float(node_info['degree']) / (n - 1) if n > 1 else 0.0
    def nombre(self): return 'cf_norm_degree_hotel'


# ============================================================
# FUNCIÓN PÚBLICA PRINCIPAL
# ============================================================

ESTRATEGIAS_CF = [
    DegreeCentralidadHotelStrategy(),
    RatioUsuariosCompartidosStrategy(),
    NormDegreeCentralidadHotelStrategy(),
]

# Nombres exportables para que pipeline.py sepa qué columnas generar
NOMBRES_METRICAS_CF = [e.nombre() for e in ESTRATEGIAS_CF]


def calcular_metricas_cf(
    json_path: Path,
    user_id: int,
    hotel_rec: int
) -> List[Dict[str, Any]]:
    """
    Calcula todas las métricas CF para un par (user, hotel_rec).

    Devuelve lista de dicts, uno por hotel compartido (explicador):
      [
        {
          'hotel_explicador': '457',
          'cf_degree_hotel': 4.0,
          'cf_ratio_usuarios_compartidos': 0.8,
          'cf_norm_degree_hotel': 0.33,
        },
        ...
      ]
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes         = data.get('nodes', [])
    relationships = data.get('relationships', [])
    index         = _build_index(nodes, relationships)

    if index['usuario_objetivo'] is None:
        print(f"  ⚠️ [CF] Sin usuario objetivo en subgrafo user={user_id}")
        return []

    filas            = []
    rels_por_fin     = index['rels_por_fin']
    usuarios_interm  = index['usuarios_intermedios']

    for h_id, h_info in index['hoteles_compartidos'].items():
        # Filtrar hoteles compartidos que no tienen valoraciones reales de usuarios intermedios
        n_valoraron = sum(
            1 for uid in rels_por_fin.get(h_id, {})
            if uid in usuarios_interm
        )
        if h_info['degree'] == 0 or n_valoraron == 0:
            continue

        hotel_real_id = h_info['properties'].get('id', h_id)
        fila = {'hotel_explicador': hotel_real_id}

        for estrategia in ESTRATEGIAS_CF:
            try:
                fila[estrategia.nombre()] = estrategia.calcular(h_id, h_info, index)
            except Exception as e:
                print(f"  ⚠️ [{estrategia.nombre()}] Error: {e}")
                fila[estrategia.nombre()] = None

        filas.append(fila)

    return filas