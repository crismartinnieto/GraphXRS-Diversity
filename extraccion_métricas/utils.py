# utils.py
import os
import json
from typing import Tuple, Dict, Set
from collections import defaultdict

def list_json_files(folder: str):
    return sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".json")])

def parse_filename_user_rec(fname: str) -> Tuple[int, int]:
    """
    Espera filename tipo: user_{user}_hotel_{rec}.json
    Si no puede parsear, devuelve (None, None)
    """
    b = os.path.basename(fname)
    name = b.replace(".json", "")
    parts = name.split("_")
    try:
        u_idx = parts.index("user") + 1
        h_idx = parts.index("hotel") + 1
        user = int(parts[u_idx])
        rec = int(parts[h_idx])
        return user, rec
    except Exception:
        return None, None

def load_subgraph(fp: str) -> dict:
    with open(fp, "r", encoding="utf-8") as fh:
        return json.load(fh)

def extract_nodes_relationships(data: dict):
    nodes = {node["id"]: node for node in data.get("nodes", [])}
    relationships = data.get("relationships", [])
    return nodes, relationships

def build_business_attr_maps(nodes: dict, relationships: list):
    """
    Devuelve:
      - business_map: node_id (str) -> business_property_id (int/str or None)
      - business_nodes: list of node_id strings que son Business
      - business_attributes: dict business_node_id -> set of attribute keys "reltype|||name"
      - attr_node_info: dict attribute_node_id -> (reltype, name)
    """
    business_map = {}
    business_nodes = []
    business_attributes = defaultdict(set)
    attr_node_info = {}

    for nid, node in nodes.items():
        if "Business" in node.get("labels", []):
            business_nodes.append(nid)
            propid = node.get("properties", {}).get("id")
            business_map[nid] = propid

    for rel in relationships:
        start = rel.get("start_node")
        end = rel.get("end_node")
        rel_type = rel.get("properties", {}).get("type", "RELATION")
        # Business -> Node
        if start in nodes and end in nodes:
            if "Business" in nodes[start].get("labels", []) and "Node" in nodes[end].get("labels", []):
                name = nodes[end].get("properties", {}).get("name")
                if name is None:
                    continue
                key = f"{rel_type}|||{name}"
                business_attributes[start].add(key)
                attr_node_info[end] = (rel_type, name)
            if "Business" in nodes[end].get("labels", []) and "Node" in nodes[start].get("labels", []):
                name = nodes[start].get("properties", {}).get("name")
                if name is None:
                    continue
                key = f"{rel_type}|||{name}"
                business_attributes[end].add(key)
                attr_node_info[start] = (rel_type, name)

    return business_map, business_nodes, business_attributes, attr_node_info
