"""
src/extraccion_metricas_conocimiento/metricas.py

Métricas XAI sobre el grafo de conocimiento (KG).
Todas las estrategias operan sobre los CSVs de explicaciones
generados a partir del subgrafo JSON temporal.

Función pública principal:
    calcular_metricas_kg(json_path, user_id, hotel_rec, hoteles_historicos)
    → dict con todas las métricas KG para el par (user, hotel_rec)
      agrupadas por hotel_explicador (histórico)
"""
import json
import ast
from abc import ABC, abstractmethod
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple


# ============================================================
# EXTRACCIÓN DE PROPIEDADES DEL SUBGRAFO JSON
# ============================================================

def _extraer_propiedades_hotel(nodes: list, relationships: list, hotel_node_id: str) -> Set[Tuple]:
    """Extrae set de (valor_propiedad, tipo_relacion) para un hotel dado su node_id interno."""
    propiedades = set()
    node_by_id  = {n['id']: n for n in nodes}

    for rel in relationships:
        start = rel.get('start_node') or rel.get('start_node_id')
        end   = rel.get('end_node')   or rel.get('end_node_id')
        if start == hotel_node_id:
            nodo_destino = node_by_id.get(end)
            if nodo_destino and 'name' in nodo_destino.get('properties', {}):
                rel_type = rel.get('properties', {}).get('type')
                propiedades.add((nodo_destino['properties']['name'], rel_type))
    return propiedades


def _parsear_subgrafo_kg(json_path: Path, hotel_rec_id: int, hoteles_historicos: List[int]):
    """
    Lee el JSON del subgrafo KG y devuelve:
      - props_recomendado: set de propiedades del hotel recomendado
      - props_por_historico: {hotel_id: set de propiedades}
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes         = data.get('nodes', [])
    relationships = data.get('relationships', [])

    hotel_rec_str = str(hotel_rec_id)
    hist_strs     = {str(h) for h in hoteles_historicos}

    props_recomendado   = set()
    props_por_historico = {}

    for node in nodes:
        if 'Business' not in node.get('labels', []):
            continue
        node_hotel_id = str(node['properties'].get('id', ''))
        props         = _extraer_propiedades_hotel(nodes, relationships, node['id'])

        if node_hotel_id == hotel_rec_str:
            props_recomendado = props
        elif node_hotel_id in hist_strs:
            props_por_historico[node_hotel_id] = props

    return props_recomendado, props_por_historico


# ============================================================
# ESTRATEGIAS (patrón Strategy)
# ============================================================

class MetricaKGStrategy(ABC):
    @abstractmethod
    def calcular(self, props_rec: Set, props_hist: Set, perfil_usuario: Dict) -> float:
        pass

    @abstractmethod
    def nombre(self) -> str:
        pass


class PropiedadesCompartidasStrategy(MetricaKGStrategy):
    def calcular(self, props_rec, props_hist, perfil_usuario):
        return float(len(props_rec & props_hist))
    def nombre(self): return 'kg_num_propiedades_compartidas'


class RatioPropiedadesCompartidasStrategy(MetricaKGStrategy):
    def calcular(self, props_rec, props_hist, perfil_usuario):
        if not props_hist:
            return 0.0
        return len(props_rec & props_hist) / len(props_hist)
    def nombre(self): return 'kg_ratio_propiedades_compartidas'


class PesoPonderadoPerfilStrategy(MetricaKGStrategy):
    def calcular(self, props_rec, props_hist, perfil_usuario):
        compartidas = [p[0] for p in (props_rec & props_hist)]
        if not compartidas or not perfil_usuario:
            return 0.0
        suma = sum(perfil_usuario.get(p, 0) for p in compartidas)
        k    = len(compartidas)
        max_posible = sum(sorted(perfil_usuario.values(), reverse=True)[:k])
        return suma / max_posible if max_posible > 0 else 0.0
    def nombre(self): return 'kg_peso_ponderado_perfil'


class SimilaridadJaccardStrategy(MetricaKGStrategy):
    def calcular(self, props_rec, props_hist, perfil_usuario):
        # Jaccard entre props del hotel recomendado y props del hotel histórico
        nombres_rec  = {p[0] for p in props_rec}
        nombres_hist = {p[0] for p in props_hist}
        union = nombres_rec | nombres_hist
        if not union:
            return 0.0
        return len(nombres_rec & nombres_hist) / len(union)
    def nombre(self): return 'kg_jaccard_similarity'


# ============================================================
# FUNCIÓN PÚBLICA PRINCIPAL
# ============================================================

ESTRATEGIAS_KG = [
    PropiedadesCompartidasStrategy(),
    RatioPropiedadesCompartidasStrategy(),
    PesoPonderadoPerfilStrategy(),
    SimilaridadJaccardStrategy(),
]

# Nombres exportables para que pipeline.py sepa qué columnas generar
NOMBRES_METRICAS_KG = [e.nombre() for e in ESTRATEGIAS_KG]


def calcular_metricas_kg(
    json_path: Path,
    user_id: int,
    hotel_rec: int,
    hoteles_historicos: List[int]
) -> Dict[str, Any]:
    """
    Calcula todas las métricas KG para un par (user, hotel_rec).

    Devuelve lista de dicts, uno por hotel histórico:
      [
        {
          'hotel_explicador': 457,
          'kg_num_propiedades_compartidas': 3,
          'kg_ratio_propiedades_compartidas': 0.27,
          ...
        },
        ...
      ]
    """
    props_rec, props_por_hist = _parsear_subgrafo_kg(json_path, hotel_rec, hoteles_historicos)

    # Perfil del usuario: frecuencia de cada propiedad en todos sus hoteles históricos
    perfil_usuario: Dict[str, int] = Counter()
    for props in props_por_hist.values():
        perfil_usuario.update(p[0] for p in props)

    filas = []
    for hotel_hist_id, props_hist in props_por_hist.items():
        fila = {'hotel_explicador': hotel_hist_id}
        for estrategia in ESTRATEGIAS_KG:
            try:
                fila[estrategia.nombre()] = estrategia.calcular(
                    props_rec, props_hist, dict(perfil_usuario)
                )
            except Exception as e:
                print(f"  ⚠️ [{estrategia.nombre()}] Error: {e}")
                fila[estrategia.nombre()] = None
        filas.append(fila)

    return filas