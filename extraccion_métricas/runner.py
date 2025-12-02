# runner.py
"""
Runner principal que orquesta:
- Construcción global de bipartito (atributos, counts)
- Cálculo de centralidades globales
- Procesamiento de cada subgrafo y cálculo de las 58 métricas
- Export CSVs detallado y agregado
"""

import os
import json
from collections import Counter, defaultdict
import numpy as np
import pandas as pd
import networkx as nx
from tqdm import tqdm

from config import INPUT_SUBGRAPHS_DIR, OUTPUT_DIR, DETAILED_CSV_NAME, AGGREGATED_CSV_NAME, TOP_K_EXAMPLES, WEIGHTS_BY_TYPE, COMPUTE_EXPENSIVE_CENTRALITIES
from utils import list_json_files, parse_filename_user_rec, load_subgraph, extract_nodes_relationships, build_business_attr_maps
import metrics_content as mcontent
import metrics_similarity as msim
import metrics_path as mpath
import metrics_centrality as mcent

# crear output
os.makedirs(OUTPUT_DIR, exist_ok=True)
DETAILED_CSV = os.path.join(OUTPUT_DIR, DETAILED_CSV_NAME)
AGGREGATED_CSV = os.path.join(OUTPUT_DIR, AGGREGATED_CSV_NAME)

# 1) SCAN GLOBAL: construir bipartito de atributos vs negocios y contar df por atributo
print("Paso 1: escaneando subgrafos para construir estadísticas globales...")
subgraph_files = list_json_files(INPUT_SUBGRAPHS_DIR)
attribute_df_counts = Counter()
attribute_global_degree = Counter()
B_global = nx.Graph()

for fp in tqdm(subgraph_files, desc="scan archivos"):
    try:
        data = load_subgraph(fp)
    except Exception as e:
        print("ERROR leyendo", fp, e)
        continue
    nodes, relationships = extract_nodes_relationships(data)
    business_map, business_nodes, business_attributes, attr_node_info = build_business_attr_maps(nodes, relationships)
    # contar atributos
    for bnode in business_nodes:
        for attr in business_attributes.get(bnode, set()):
            attribute_df_counts[attr] += 1
            attribute_global_degree[attr] += 1
            B_global.add_node(f"BUS_{bnode}", bipartite=0)
            B_global.add_node(f"ATTR_{attr}", bipartite=1)
            B_global.add_edge(f"BUS_{bnode}", f"ATTR_{attr}")

# N de negocios aproximado
N_businesses = len([n for n in B_global.nodes() if isinstance(n, str) and n.startswith("BUS_")])
if N_businesses == 0:
    # fallback: contar archivos * 1? mejor dejar 1 para evitar zero division
    N_businesses = max(1, len(subgraph_files))

print(f"Hoteles detectados (aprox): {N_businesses}")
print(f"Atributos detectados: {len(attribute_df_counts)}")

# IDF global
idf = mcontent.compute_idf(attribute_df_counts, N_businesses)

# centralidades globales (pagerank, eigenvector, betweenness) - pueden ser costosas
pagerank = {}
eigen = {}
betweenness = {}
if COMPUTE_EXPENSIVE_CENTRALITIES:
    try:
        print("Calculando PageRank global (puede tardar)...")
        pagerank = nx.pagerank(B_global, alpha=0.85)
    except Exception as e:
        print("pagerank fallo:", e)
        pagerank = {}
    try:
        print("Calculando eigenvector (numpy) global (puede tardar)...")
        eigen = nx.eigenvector_centrality_numpy(B_global)
    except Exception as e:
        print("eigenvector fallo:", e)
        eigen = {}
    try:
        print("Calculando betweenness (puede tardar mucho)...")
        betweenness = nx.betweenness_centrality(B_global)
    except Exception as e:
        print("betweenness fallo:", e)
        betweenness = {}

# 2) PROCESAR CADA SUBGRAFO y calcular métricas por fila
detailed_rows = []
aggregated = defaultdict(lambda: {
    "num_consumed": 0,
    "mean_jaccard_vals": [],
    "max_jaccard": -1,
    "min_jaccard": 2,
    "explanation_types_used": set(),
    "support_counts": Counter(),
    "popularity_vals": [],
    "novel_count": 0
})

print("Paso 2: procesando subgrafos y calculando métricas por fila...")
for fp in tqdm(subgraph_files, desc="procesando subgrafos"):
    user_id, rec_hotel = parse_filename_user_rec(fp)
    try:
        data = load_subgraph(fp)
    except Exception:
        continue
    nodes, relationships = extract_nodes_relationships(data)
    business_map, business_nodes, business_attributes, attr_node_info = build_business_attr_maps(nodes, relationships)

    # detectar nodo recomendado (por property id) si es posible
    rec_node = None
    for nid, pid in business_map.items():
        try:
            if pid is not None and int(pid) == int(rec_hotel):
                rec_node = nid
                break
        except Exception:
            pass
    if rec_node is None and business_nodes:
        # heurística: si el filename indica rec_hotel pero no está, tomar el último Business
        rec_node = business_nodes[-1]

    consumed_nodes = [n for n in business_nodes if n != rec_node]
    aggregated[(user_id, rec_hotel)]["num_consumed"] = len(consumed_nodes)
    rec_attrs = business_attributes.get(rec_node, set())

    consumed_attr_sets = {nid: business_attributes.get(nid, set()) for nid in consumed_nodes}
    consumed_union = set().union(*consumed_attr_sets.values()) if consumed_attr_sets else set()

    # Precompute vectors for cosine (universal attr list for this subgraph)
    all_attr_keys = sorted(set(list(rec_attrs) + list(consumed_union)))
    attr_index = {a: idx for idx, a in enumerate(all_attr_keys)}
    def vec_from_attrset(s):
        v = np.zeros(len(all_attr_keys), dtype=int)
        for a in s:
            if a in attr_index:
                v[attr_index[a]] = 1
        return v

    rec_vec = vec_from_attrset(rec_attrs)

    # Example-based aggregated helpers
    best_sim = -1
    worst_sim = 2
    sim_list = []
    for cnode, cattrs in consumed_attr_sets.items():
        jacc = msim.jaccard_similarity(rec_attrs, cattrs)
        sim_list.append(jacc)
        if jacc > best_sim:
            best_sim = jacc
        if jacc < worst_sim:
            worst_sim = jacc

    mean_sim = float(np.mean(sim_list)) if sim_list else 0.0
    kstrength = msim.k_nearest_example_strength(rec_attrs, consumed_attr_sets, k=TOP_K_EXAMPLES)
    proto_sim, proto_node = msim.prototype_similarity(consumed_attr_sets, rec_attrs)
    consensus_mean, consensus_var = msim.example_consensus_score(consumed_attr_sets, rec_attrs)

    # iterate per consumed and per property of rec (para mantener la estructura mínima)
    # Si no hay propiedades en rec, generamos al menos una fila por consumed con property vacía
    props_iter = rec_attrs if rec_attrs else {None}
    for cnode, cattrs in consumed_attr_sets.items() if consumed_attr_sets else [(None, set())]:
        for prop in props_iter:
            row = {}
            row["usuario_objetivo"] = user_id
            row["hotel_recomendado"] = rec_hotel
            if prop is not None:
                p_type, p_name = prop.split("|||",1) if "|||" in prop else (None, prop)
            else:
                p_type, p_name = None, None
            row["propiedad_type"] = p_type
            row["propiedad_name"] = p_name
            # item consumido info
            row["item_consumido_node"] = cnode
            row["item_consumido_hotelid"] = business_map.get(cnode) if cnode else None

            # CONTENT METRICS
            support = mcontent.attribute_tf_user(prop, consumed_nodes, business_attributes) if prop is not None else 0
            row["support_count"] = support
            row["amf"] = mcontent.attribute_match_frequency(prop, consumed_nodes, business_attributes) if prop is not None else 0.0
            row["tf_user"] = support
            row["idf"] = idf.get(prop, np.nan) if prop is not None else np.nan
            row["tf_idf_user"] = mcontent.tf_idf_user(row["tf_user"], row["idf"])
            row["novelty"] = mcontent.attribute_novelty(prop, row["tf_user"]) if prop is not None else 1
            row["specificity"] = mcontent.attribute_specificity(attribute_global_degree.get(prop, 1)) if prop is not None else 0.0
            row["attribute_overlap_count"] = mcontent.attribute_overlap_count(rec_attrs, cattrs)
            row["attribute_overlap_ratio"] = mcontent.attribute_overlap_ratio(rec_attrs, cattrs)
            row["novelty_count_rec"] = mcontent.novelty_count(rec_attrs, consumed_union)
            row["novelty_ratio_rec"] = mcontent.novelty_ratio(rec_attrs, consumed_union)

            # SIMILARITY METRICS
            row["jaccard_similarity"] = msim.jaccard_similarity(rec_attrs, cattrs)
            cvec = vec_from_attrset(cattrs)
            row["cosine_similarity"] = msim.cosine_similarity_from_vectors(rec_vec, cvec)
            row["shared_attributes_count"] = len(rec_attrs & cattrs)
            # shared by type counts
            shared_by_type = {}
            for s in (rec_attrs & cattrs):
                if "|||" in s:
                    tt, _ = s.split("|||",1)
                    shared_by_type[tt] = shared_by_type.get(tt, 0) + 1
            # fill common types
            for common in ["has_category","located_in_city","has_attribute","has_rating","has_postal_code"]:
                row[f"shared_count_type__{common}"] = shared_by_type.get(common, 0)

            # WEIGHTED SHARED SCORE
            weighted_shared = 0.0
            for t,cnt in shared_by_type.items():
                weighted_shared += WEIGHTS_BY_TYPE.get(t, 1.0) * cnt
            row["weighted_shared_score"] = weighted_shared

            # PATH METRICS
            shared = rec_attrs & cattrs
            row["path_length"] = mpath.path_length_between_businesses(shared)
            row["path_count"] = mpath.path_count(shared)
            path_variety_count, path_types = mpath.path_type_variety(shared)
            row["path_type_variety"] = path_variety_count
            row["path_types"] = ";".join(sorted(list(path_types))) if path_types else ""
            row["path_type_frequency"] = json.dump((mpath.path_type_frequency(shared)))
            row["path_confidence_score"] = mpath.path_confidence_score(shared, WEIGHTS_BY_TYPE)

            # EXAMPLE-BASED METRICS (per-row we include many, some are repeated across rows)
            row["best_example_similarity"] = best_sim
            row["worst_example_similarity"] = worst_sim
            row["mean_example_similarity"] = mean_sim
            row["k_nearest_example_strength"] = kstrength
            row["prototype_similarity"] = proto_sim
            row["prototype_node"] = proto_node
            row["example_consensus_mean"] = consensus_mean
            row["example_consensus_var"] = consensus_var
            row["example_coverage"] = sum(1 for a_set in consumed_attr_sets.values() if len(a_set & rec_attrs)>0) / max(1, len(consumed_attr_sets))
            row["example_density_avg_support_per_attr"] = float(np.mean([ sum(1 for s in consumed_attr_sets.values() if prop in s) for prop in (rec_attrs if rec_attrs else [None]) ])) if rec_attrs else 0.0

            # POPULARITY / CENTRALITY
            if prop is not None:
                row["popularity_degree"] = attribute_global_degree.get(prop, 0)
                row["popularity_percentile"] = sum(1 for v in attribute_df_counts.values() if v <= attribute_df_counts.get(prop,0)) / max(1, len(attribute_df_counts))
                row["degree_centrality_raw"] = mcent.degree_centrality_raw(B_global, prop)
                row["degree_centrality_norm"] = mcent.degree_centrality_normalized(B_global, prop)
                row["pagerank_attr"] = mcent.pagerank_attr(pagerank, prop)
                row["eigenvector_attr"] = mcent.eigenvector_attr(eigen, prop)
                row["betweenness_attr"] = mcent.betweenness_attr(betweenness, prop)
                row["harmonic_centrality"] = mcent.harmonic_centrality(B_global, prop) if COMPUTE_EXPENSIVE_CENTRALITIES else 0.0
                row["clustering_coefficient_attr"] = mcent.clustering_coefficient_on_projection(B_global, prop) if COMPUTE_EXPENSIVE_CENTRALITIES else 0.0
                row["attribute_influence_score"] = mcent.attribute_influence_score(row["popularity_degree"], row["amf"])
            else:
                for cname in ["popularity_degree","popularity_percentile","degree_centrality_raw","degree_centrality_norm","pagerank_attr","eigenvector_attr","betweenness_attr","harmonic_centrality","clustering_coefficient_attr","attribute_influence_score"]:
                    row[cname] = np.nan

            # DIVERSITY / COVERAGE / BLIND-SPOT
            row["explanation_type_diversity"] = len(set([pt for pt in [p_type] if pt]))
            row["preference_coverage"] = mcontent.attribute_presence_ratio(rec_attrs, consumed_union)
            row["blind_spot_coverage"] = 1.0 - row["preference_coverage"]
            row["novelty_ratio"] = mcontent.novelty_ratio(rec_attrs, consumed_union)
            row["surprise_mean"] = row.get("surprise_mean", 0.0) if "surprise_mean" in row else 0.0

            # AGGREGATION STORING for later
            aggkey = (user_id, rec_hotel)
            aggregated[aggkey]["mean_jaccard_vals"].append(row["jaccard_similarity"])
            aggregated[aggkey]["explanation_types_used"].add(p_type)
            aggregated[aggkey]["support_counts"].update({prop: support})
            if row.get("popularity_degree") and not np.isnan(row.get("popularity_degree")):
                aggregated[aggkey]["popularity_vals"].append(row.get("popularity_degree"))
            if row.get("novelty", 0)==1:
                aggregated[aggkey]["novel_count"] += 1

            detailed_rows.append(row)

# 3) Construir DataFrames y escribir CSVs
print("Paso 3: escribiendo CSVs...")
df_detail = pd.DataFrame(detailed_rows)
# columnas mínimas solicitadas
min_cols = ["usuario_objetivo","hotel_recomendado","propiedad_name","item_consumido_hotelid"]
for c in min_cols:
    if c not in df_detail.columns:
        df_detail[c] = None

df_detail.to_csv(DETAILED_CSV, index=False, encoding="utf-8")
print("CSV detallado guardado en:", DETAILED_CSV)

# aggregated
agg_rows = []
for (user, rec), info in aggregated.items():
    row = {
        "usuario_objetivo": user,
        "hotel_recomendado": rec,
        "num_consumed": info["num_consumed"],
        "mean_jaccard": float(np.mean(info["mean_jaccard_vals"])) if info["mean_jaccard_vals"] else np.nan,
        "max_jaccard": float(np.max(info["mean_jaccard_vals"])) if info["mean_jaccard_vals"] else np.nan,
        "min_jaccard": float(np.min(info["mean_jaccard_vals"])) if info["mean_jaccard_vals"] else np.nan,
        "explanation_type_diversity": len(info["explanation_types_used"]),
        "avg_popularity": float(np.mean(info["popularity_vals"])) if info["popularity_vals"] else np.nan,
        "novel_attributes_count": info["novel_count"]
    }
    # top supported
    for i, (attr, cnt) in enumerate(info["support_counts"].most_common(5), 1):
        row[f"top_supported_attr_{i}"] = attr
        row[f"top_supported_count_{i}"] = cnt
    agg_rows.append(row)

df_agg = pd.DataFrame(agg_rows)
df_agg.to_csv(AGGREGATED_CSV, index=False, encoding="utf-8")
print("CSV agregado guardado en:", AGGREGATED_CSV)

print("Proceso finalizado. Revisa los CSVs.")
