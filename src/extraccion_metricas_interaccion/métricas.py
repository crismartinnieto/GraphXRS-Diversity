"""
src/extraccion_metricas_interaccion/métricas.py

Define TODAS las clases y funciones necesarias para calcular métricas
de centralidad sobre subgrafos de interacción.

CONTIENE:
  - Funciones de utilidad (load_subgraph, build_graph_index)
  - Clase abstracta (CentralidadStrategy)
  - Estrategias concretas (5 métricas)
  - Calculador coordinador (CalculadorCentralidades)

Para añadir una métrica nueva:
  1. Crea una clase que herede de CentralidadStrategy
  2. Implementa calcular() y nombre()
  3. Añádela a la lista en xaigraph.py → _cargar_estrategias()
"""
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Any
import json
from pathlib import Path
import sys

# ============================================================
# MODE: 'muestra' o 'completo'
# ============================================================
MODE = "muestra"  # Cambiar a "completo" para procesar todos los usuarios

# ============================================================
# DEFINICIÓN DE RUTAS RELATIVAS (desde la ubicación de este script)
# ============================================================
# Este script está en: src/extraccion_metricas_interaccion/métricas.py
SCRIPT_DIR = Path(__file__).resolve().parent  # .../extraccion_metricas_interaccion/

# Subir niveles hasta llegar a la raíz
# ../  → src/
# ../../  → raíz del proyecto
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Definir rutas relativas desde la raíz
DATA_DIR = PROJECT_ROOT / "data"
SUBGRAFOS_INTERACCIONES = DATA_DIR / f"subgrafos_interacciones_{MODE}"


# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def load_subgraph(filepath: Path):
    """
    Carga nodos y relaciones desde un JSON de subgrafo.
    
    Args:
        filepath: Ruta al archivo JSON del subgrafo
        
    Returns:
        Tupla (nodes, relationships) con los datos del subgrafo
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('nodes', []), data.get('relationships', [])


def build_graph_index(nodes, relationships):
    """
    Construye índices rápidos a partir del JSON del subgrafo.

    Args:
        nodes: Lista de nodos del grafo
        relationships: Lista de relaciones del grafo
        
    Returns:
        Tupla con:
            - node_info: {node_id: {degree, labels, properties}}
            - relaciones_por_inicio: {node_id: {vecino_id: rating}}
            - relaciones_por_fin: {node_id: {vecino_id: rating}}
            - usuario_objetivo: (node_id, info) o None
            - hotel_recomendado: (node_id, info) o None
            - usuarios_intermedios: {node_id: info}
            - hoteles_compartidos: {node_id: info}
    """
    degree_count = defaultdict(int)
    node_info: Dict[str, Dict] = {}

    for node in nodes:
        nid = node['id']
        node_info[nid] = {
            'degree': 0,
            'labels': node.get('labels', []),
            'properties': node.get('properties', {})
        }

    relaciones_por_inicio: Dict[str, Dict] = defaultdict(dict)
    relaciones_por_fin: Dict[str, Dict] = defaultdict(dict)

    for rel in relationships:
        s = rel['start_node_id']
        e = rel['end_node_id']
        rating = rel.get('properties', {}).get('rating', None)
        degree_count[s] += 1
        degree_count[e] += 1
        relaciones_por_inicio[s][e] = rating
        relaciones_por_fin[e][s] = rating

    for nid, cnt in degree_count.items():
        if nid in node_info:
            node_info[nid]['degree'] = cnt

    usuario_objetivo = None
    hotel_recomendado = None
    usuarios_intermedios: Dict[str, Dict] = {}
    hoteles_compartidos: Dict[str, Dict] = {}

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

    return (node_info, relaciones_por_inicio, relaciones_por_fin,
            usuario_objetivo, hotel_recomendado,
            usuarios_intermedios, hoteles_compartidos)


# ============================================================
# CLASE ABSTRACTA
# ============================================================

class CentralidadStrategy(ABC):
    """
    Interfaz Strategy para métricas de centralidad de hoteles compartidos.
    Cada estrategia concreta calcula una métrica para un hotel explicador.
    """

    @abstractmethod
    def calcular(self, node_id: str, node_info: Dict, index: tuple) -> float:
        """
        Args:
            node_id: ID interno del nodo hotel compartido
            node_info: {degree, labels, properties}
            index: Tupla completa de build_graph_index()
        Returns:
            Valor float de la métrica.
        """
        pass

    @abstractmethod
    def nombre(self) -> str:
        """Nombre de la métrica — será la columna en el CSV de salida."""
        pass


# ============================================================
# ESTRATEGIAS CONCRETAS
# ============================================================

class DegreeCentralidadHotelStrategy(CentralidadStrategy):
    """
    Degree bruto del hotel compartido.
    Mide popularidad: cuántas valoraciones tiene en el subgrafo.
    """
    def calcular(self, node_id, node_info, index):
        return float(node_info['degree'])

    def nombre(self):
        return 'degree_hotel'


class RatioUsuariosCompartidosStrategy(CentralidadStrategy):
    """
    Fracción de usuarios intermedios del subgrafo que valoraron este hotel.
    Valor en [0,1]. Cercano a 1 → muchos usuarios similares lo valoraron.
    """
    def calcular(self, node_id, node_info, index):
        (_, _inicio, relaciones_por_fin,
         _uobj, _hrec, usuarios_intermedios, _hcomp) = index

        if not usuarios_intermedios:
            return 0.0

        usuarios_que_valoraron = sum(
            1 for uid in relaciones_por_fin.get(node_id, {})
            if uid in usuarios_intermedios
        )
        return usuarios_que_valoraron / len(usuarios_intermedios)

    def nombre(self):
        return 'ratio_usuarios_compartidos'


class NumUsuariosCompartidosStrategy(CentralidadStrategy):
    """
    Número absoluto de usuarios intermedios que valoraron este hotel.
    Complementa RatioUsuariosCompartidosStrategy con el valor bruto.
    """
    def calcular(self, node_id, node_info, index):
        (_, _inicio, relaciones_por_fin,
         _uobj, _hrec, usuarios_intermedios, _hcomp) = index

        return float(sum(
            1 for uid in relaciones_por_fin.get(node_id, {})
            if uid in usuarios_intermedios
        ))

    def nombre(self):
        return 'num_usuarios_compartidos'


class PesoMedioRatingHotelStrategy(CentralidadStrategy):
    """
    Rating medio de todas las valoraciones que recibió este hotel compartido.
    Mide la calidad percibida por los usuarios intermedios.
    """
    def calcular(self, node_id, node_info, index):
        (_, _inicio, relaciones_por_fin, *_) = index

        ratings = [
            r for r in relaciones_por_fin.get(node_id, {}).values()
            if r is not None
        ]
        return sum(ratings) / len(ratings) if ratings else 0.0

    def nombre(self):
        return 'rating_medio_hotel'


class NormDegreeCentralidadHotelStrategy(CentralidadStrategy):
    """
    Degree del hotel normalizado por (total de nodos del subgrafo - 1).
    Permite comparar entre subgrafos de distinto tamaño.
    """
    def calcular(self, node_id, node_info, index):
        n = len(index[0])
        return float(node_info['degree']) / (n - 1) if n > 1 else 0.0

    def nombre(self):
        return 'norm_degree_hotel'


# ============================================================
# CALCULADOR COORDINADOR
# ============================================================

class CalculadorCentralidades:
    """
    Coordinador de cálculo de métricas de interacción.
    Aplica estrategias de centralidad sobre subgrafos JSON.
    """

    def __init__(self):
        self.estrategias: List[CentralidadStrategy] = []

    def agregar_estrategia(self, e: CentralidadStrategy):
        """Añade una estrategia al calculador."""
        self.estrategias.append(e)

    def agregar_estrategias(self, estrategias: List[CentralidadStrategy]):
        """Añade múltiples estrategias al calculador."""
        self.estrategias.extend(estrategias)

    def limpiar_estrategias(self):
        """Elimina todas las estrategias."""
        self.estrategias = []

    def _calcular_fila(self, usuario_real_id, recommended_hotel,
                      hotel_real_id, node_id, node_info, index) -> Dict[str, Any]:
        """
        Calcula todas las estrategias para un hotel compartido.
        
        Returns:
            Diccionario con usuario, hotel_recomendado, hotel_compartido y métricas
        """
        fila = {
            'usuario': usuario_real_id,
            'hotel_recomendado': recommended_hotel,
            'hotel_compartido': hotel_real_id,
        }
        for estrategia in self.estrategias:
            try:
                fila[estrategia.nombre()] = estrategia.calcular(
                    node_id, node_info, index
                )
            except Exception as e:
                print(f"⚠️ Error en {estrategia.nombre()}: {e}")
                fila[estrategia.nombre()] = None
        return fila

    def calcular_para_subgrafo(self, json_path: Path,
                              csv_user_id, recommended_hotel) -> List[Dict]:
        """
        Procesa un subgrafo JSON y devuelve métricas para sus hoteles compartidos.
        
        Args:
            json_path: Ruta al JSON del subgrafo
            csv_user_id: ID del usuario
            recommended_hotel: Hotel recomendado
            
        Returns:
            Lista de diccionarios, uno por hotel compartido válido
        """
        nodes, relationships = load_subgraph(json_path)
        index = build_graph_index(nodes, relationships)

        (_, relaciones_por_inicio, relaciones_por_fin,
         usuario_objetivo, hotel_recomendado,
         usuarios_intermedios, hoteles_compartidos) = index

        if usuario_objetivo is None:
            print(f"  ⚠️ Sin usuario objetivo en {json_path.name}")
            return []

        usuario_real_id = usuario_objetivo[1]['properties'].get(
            'id', usuario_objetivo[0]
        )
        filas = []

        for h_id, h_info in hoteles_compartidos.items():
            hotel_real_id = h_info['properties'].get('id', h_id)
            usuarios_que_val = sum(
                1 for uid in relaciones_por_fin.get(h_id, {})
                if uid in usuarios_intermedios
            )
            if h_info['degree'] > 0 and usuarios_que_val > 0:
                filas.append(self._calcular_fila(
                    usuario_real_id, recommended_hotel,
                    hotel_real_id, h_id, h_info, index
                ))

        return filas

    def calcular_para_usuario(self, usuario_id) -> List[Dict]:
        """
        Procesa todos los JSONs de un usuario y devuelve todas las métricas.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Lista de diccionarios con todas las combinaciones calculadas
        """
        json_files = list(SUBGRAFOS_INTERACCIONES.glob(
            f"user_{usuario_id}_hotel_*_interactions.json"
        ))

        if not json_files:
            raise FileNotFoundError(
                f"No hay JSONs para usuario {usuario_id} en "
                f"{SUBGRAFOS_INTERACCIONES}"
            )

        print(f"  📊 {len(json_files)} subgrafos para usuario {usuario_id}")

        todas = []
        for json_path in json_files:
            recommended_hotel = json_path.stem.split('_')[3]
            todas.extend(self.calcular_para_subgrafo(
                json_path, usuario_id, recommended_hotel
            ))

        return todas