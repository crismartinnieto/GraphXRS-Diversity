"""
Runner principal para extraer todas las métricas de explicabilidad
Con organización por usuario y consolidación de CSVs por granularidad
"""
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List
import json
import traceback
from collections import defaultdict

from config import SUBGRAPHS_DIR, OUTPUT_DIR
from utils import (load_subgraph, parse_filename, get_user_consumed_hotels, 
                   identify_recommended_hotel, get_business_property_id)
from metrics_wrapper import convert_results_to_business_ids, create_consumed_mapping

# Importar todos los módulos de métricas
from metrics_path import compute_all_path_metrics
from metrics_centrality import compute_all_centrality_metrics
from metrics_content import compute_all_content_metrics
from metrics_examples import compute_all_example_metrics
from metrics_similarity import compute_all_similarity_metrics
from metrics_popularity import compute_all_popularity_metrics
from metrics_diversity import compute_all_diversity_metrics
from metrics_novelty import compute_all_novelty_metrics
from metrics_coverage import compute_all_coverage_metrics


def process_single_subgraph(filepath: str) -> Dict[str, List[Dict]]:
    """
    Procesa un único subgrafo y extrae todas las métricas.
    
    Returns:
        Dict con listas de resultados por categoría de métrica
    """
    filename = os.path.basename(filepath)
    print(f"\n{'='*80}")
    print(f"Procesando: {filename}")
    print(f"{'='*80}")
    
    try:
        # Parsear nombre de archivo
        user_id, hotel_id_from_file = parse_filename(filename)
        
        # Cargar subgrafo
        subgraph = load_subgraph(filepath)
        
        # Identificar hotel recomendado (node_id interno)
        hotel_rec_node_id = identify_recommended_hotel(subgraph, hotel_id_from_file)
        if not hotel_rec_node_id:
            print(f"⚠️  No se encontró hotel recomendado en {filename}")
            return {}
        
        # Identificar hoteles consumidos (node_ids internos)
        consumed_hotels_node_ids = get_user_consumed_hotels(subgraph, hotel_rec_node_id)
        
        # Crear mapeo de node_ids a business_ids
        consumed_mapping = create_consumed_mapping(subgraph, consumed_hotels_node_ids)
        
        print(f"✓ Usuario: {user_id}")
        print(f"✓ Hotel recomendado (ID negocio): {hotel_id_from_file}")
        print(f"✓ Hotel recomendado (node_id): {hotel_rec_node_id}")
        print(f"✓ Hoteles consumidos: {len(consumed_hotels_node_ids)}")
        
        if not consumed_hotels_node_ids:
            print(f"⚠️  No hay hoteles consumidos para el usuario {user_id}")
            return {}
        
        # Calcular métricas AMF para usar en centralidad
        from metrics_content import attribute_match_frequency
        from utils import get_connected_properties
        
        amf_scores = {}
        rec_props = get_connected_properties(subgraph, hotel_rec_node_id)
        for rel_type, values in rec_props.items():
            for prop_value in values:
                # Encontrar node_id
                for node in subgraph['nodes']:
                    if node.get('properties', {}).get('name') == prop_value:
                        amf = attribute_match_frequency(subgraph, consumed_hotels_node_ids, rel_type, prop_value)
                        amf_scores[node['id']] = amf
                        break
        
        results = {}
        
        # 1. Métricas de caminos
        print("\n[1/9] Calculando métricas de caminos...")
        try:
            path_results = compute_all_path_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['path'] = convert_results_to_business_ids(subgraph, path_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['path'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['path'] = []
        
        # 2. Métricas de centralidad
        print("[2/9] Calculando métricas de centralidad...")
        try:
            centrality_results = compute_all_centrality_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids, amf_scores)
            results['centrality'] = convert_results_to_business_ids(subgraph, centrality_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['centrality'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['centrality'] = []
        
        # 3. Métricas de contenido/atributos
        print("[3/9] Calculando métricas de contenido...")
        try:
            content_results = compute_all_content_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['content'] = convert_results_to_business_ids(subgraph, content_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['content'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['content'] = []
        
        # 4. Métricas basadas en ejemplos
        print("[4/9] Calculando métricas de ejemplos...")
        try:
            examples_results = compute_all_example_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['examples'] = convert_results_to_business_ids(subgraph, examples_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['examples'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['examples'] = []
        
        # 5. Métricas de similitud
        print("[5/9] Calculando métricas de similitud...")
        try:
            similarity_results = compute_all_similarity_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['similarity'] = convert_results_to_business_ids(subgraph, similarity_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['similarity'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['similarity'] = []
        
        # 6. Métricas de popularidad
        print("[6/9] Calculando métricas de popularidad...")
        try:
            popularity_results = compute_all_popularity_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['popularity'] = convert_results_to_business_ids(subgraph, popularity_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['popularity'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['popularity'] = []
        
        # 7. Métricas de diversidad
        print("[7/9] Calculando métricas de diversidad...")
        try:
            diversity_results = compute_all_diversity_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['diversity'] = convert_results_to_business_ids(subgraph, diversity_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['diversity'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['diversity'] = []
        
        # 8. Métricas de novedad
        print("[8/9] Calculando métricas de novedad...")
        try:
            novelty_results = compute_all_novelty_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['novelty'] = convert_results_to_business_ids(subgraph, novelty_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['novelty'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['novelty'] = []
        
        # 9. Métricas de cobertura
        print("[9/9] Calculando métricas de cobertura...")
        try:
            coverage_results = compute_all_coverage_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['coverage'] = convert_results_to_business_ids(subgraph, coverage_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['coverage'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['coverage'] = []
                    
        print(f"\n✅ Procesamiento completado para {filename}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO procesando {filename}")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        traceback.print_exc()
        return {}


def merge_dataframes_by_columns(dfs: List[pd.DataFrame], name: str) -> pd.DataFrame:
    """
    Combina múltiples DataFrames que comparten columnas comunes.
    Hace un merge inteligente manteniendo las columnas únicas de cada uno.
    """
    if not dfs:
        return pd.DataFrame()
    
    if len(dfs) == 1:
        return dfs[0]
    
    print(f"\n   Consolidando {name}:")
    for i, df in enumerate(dfs):
        print(f"     - DF {i+1}: {len(df)} filas, {len(df.columns)} columnas")
    
    # Identificar columnas comunes (keys para merge)
    common_cols = set(dfs[0].columns)
    for df in dfs[1:]:
        common_cols &= set(df.columns)
    
    # Las columnas comunes típicas son: usuario, hotel_recomendado, hotel_consumido, propiedad
    merge_keys = [col for col in ['usuario', 'hotel_recomendado', 'hotel_consumido', 'propiedad'] 
                  if col in common_cols]
    
    print(f"     - Columnas para merge: {merge_keys}")
    
    # Hacer merge progresivo
    result = dfs[0]
    for i, df in enumerate(dfs[1:], 2):
        result = pd.merge(result, df, on=merge_keys, how='outer', suffixes=('', f'_dup{i}'))
    
    print(f"     ✓ Resultado: {len(result)} filas, {len(result.columns)} columnas")
    return result


def save_consolidated_metrics_by_user(all_results_by_user: Dict[int, Dict[str, List[Dict]]], 
                                      output_base_dir: str):
    """
    Guarda métricas consolidadas por usuario en carpetas separadas.
    
    Estructura de salida:
    - metricas_usuario_X/
      - metricas_nivel_propiedad.csv (centrality + content + popularity)
      - metricas_nivel_ejemplo.csv (examples + similarity + diversity)
      - metricas_caminos.csv (path)
      - metricas_globales.csv (novelty + coverage)
    """
    
    for user_id, results in all_results_by_user.items():
        # Crear carpeta del usuario
        user_dir = os.path.join(output_base_dir, f"metricas_usuario_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        print(f"\n{'='*80}")
        print(f"💾 Guardando métricas para Usuario {user_id}")
        print(f"{'='*80}")
        
        # ===== 1. NIVEL PROPIEDAD (992 filas) =====
        print("\n[1/4] Consolidando métricas nivel propiedad...")
        property_dfs = []
        for metric_type in ['centrality', 'content', 'popularity']:
            if results.get(metric_type):
                df = pd.DataFrame(results[metric_type])
                property_dfs.append(df)
        
        if property_dfs:
            merged_property = merge_dataframes_by_columns(property_dfs, "nivel propiedad")
            output_path = os.path.join(user_dir, "metricas_nivel_propiedad.csv")
            merged_property.to_csv(output_path, index=False, encoding='utf-8')
            print(f"   ✓ Guardado: {output_path} ({len(merged_property)} filas)")
        
        # ===== 2. NIVEL EJEMPLO (200 filas) =====
        print("\n[2/4] Consolidando métricas nivel ejemplo...")
        example_dfs = []
        for metric_type in ['examples', 'similarity', 'diversity']:
            if results.get(metric_type):
                df = pd.DataFrame(results[metric_type])
                example_dfs.append(df)
        
        if example_dfs:
            merged_example = merge_dataframes_by_columns(example_dfs, "nivel ejemplo")
            output_path = os.path.join(user_dir, "metricas_nivel_ejemplo.csv")
            merged_example.to_csv(output_path, index=False, encoding='utf-8')
            print(f"   ✓ Guardado: {output_path} ({len(merged_example)} filas)")
        
        # ===== 3. CAMINOS (703 filas) =====
        print("\n[3/4] Guardando métricas de caminos...")
        if results.get('path'):
            df_path = pd.DataFrame(results['path'])
            output_path = os.path.join(user_dir, "metricas_caminos.csv")
            df_path.to_csv(output_path, index=False, encoding='utf-8')
            print(f"   ✓ Guardado: {output_path} ({len(df_path)} filas)")
        
        # ===== 4. NIVEL GLOBAL (50 filas) =====
        print("\n[4/4] Consolidando métricas globales...")
        global_dfs = []
        for metric_type in ['novelty', 'coverage']:
            if results.get(metric_type):
                df = pd.DataFrame(results[metric_type])
                global_dfs.append(df)
        
        if global_dfs:
            merged_global = merge_dataframes_by_columns(global_dfs, "globales")
            output_path = os.path.join(user_dir, "metricas_globales.csv")
            merged_global.to_csv(output_path, index=False, encoding='utf-8')
            print(f"   ✓ Guardado: {output_path} ({len(merged_global)} filas)")


def run_all_subgraphs(limit: int = None):
    """
    Procesa todos los subgrafos en el directorio.
    
    Args:
        limit: Limitar a los primeros N archivos (útil para testing)
    """
    # Crear directorio de salida si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Listar todos los archivos JSON
    try:
        subgraph_files = [
            f for f in os.listdir(SUBGRAPHS_DIR) 
            if f.endswith('.json') and f.startswith('user_')
        ]
    except Exception as e:
        print(f"❌ Error listando archivos en {SUBGRAPHS_DIR}: {str(e)}")
        return
    
    if not subgraph_files:
        print(f"⚠️  No se encontraron archivos JSON en {SUBGRAPHS_DIR}")
        return
    
    if limit:
        subgraph_files = subgraph_files[:limit]
    
    print(f"\n{'#'*80}")
    print(f"# EXTRACCIÓN DE MÉTRICAS DE EXPLICABILIDAD")
    print(f"{'#'*80}")
    print(f"\n📁 Directorio de entrada: {SUBGRAPHS_DIR}")
    print(f"📊 Archivos encontrados: {len(subgraph_files)}")
    print(f"💾 Directorio de salida: {OUTPUT_DIR}")
    
    if limit:
        print(f"⚠️  MODO TEST: Procesando solo los primeros {limit} archivos")
    
    # Acumuladores por USUARIO
    results_by_user = defaultdict(lambda: {
        'path': [],
        'centrality': [],
        'content': [],
        'examples': [],
        'similarity': [],
        'popularity': [],
        'diversity': [],
        'novelty': [],
        'coverage': []
    })
    
    # Estadísticas
    successful = 0
    failed = 0
    
    # Procesar cada subgrafo
    for i, filename in enumerate(subgraph_files, 1):
        filepath = os.path.join(SUBGRAPHS_DIR, filename)
        
        print(f"\n{'─'*80}")
        print(f"Progreso: {i}/{len(subgraph_files)} ({i/len(subgraph_files)*100:.1f}%)")
        
        try:
            # Obtener user_id del filename
            user_id, _ = parse_filename(filename)
            
            results = process_single_subgraph(filepath)
            
            if results:
                # Acumular resultados POR USUARIO
                for category, data in results.items():
                    results_by_user[user_id][category].extend(data)
                successful += 1
            else:
                failed += 1
        
        except Exception as e:
            print(f"❌ ERROR INESPERADO procesando {filename}: {str(e)}")
            traceback.print_exc()
            failed += 1
            continue
    
    # Guardar CSVs consolidados por usuario
    print(f"\n{'='*80}")
    print("GUARDANDO RESULTADOS CONSOLIDADOS POR USUARIO...")
    print(f"{'='*80}\n")
    
    save_consolidated_metrics_by_user(results_by_user, OUTPUT_DIR)
    
    print(f"\n{'#'*80}")
    print("# ✅ PROCESO COMPLETADO")
    print(f"{'#'*80}\n")
    
    # Resumen final
    print("RESUMEN DE PROCESAMIENTO:")
    print(f"{'─'*80}")
    print(f"  • Archivos procesados exitosamente: {successful}")
    print(f"  • Archivos con errores: {failed}")
    print(f"  • Total: {successful + failed}")
    print(f"  • Usuarios únicos: {len(results_by_user)}")
    print(f"{'─'*80}\n")
    
    print("ESTRUCTURA DE SALIDA:")
    print(f"{'─'*80}")
    for user_id in sorted(results_by_user.keys()):
        print(f"\n  📁 metricas_usuario_{user_id}/")
        user_results = results_by_user[user_id]
        
        # Contar filas por tipo
        prop_count = len(user_results['centrality']) or len(user_results['content']) or len(user_results['popularity'])
        example_count = len(user_results['examples']) or len(user_results['similarity']) or len(user_results['diversity'])
        path_count = len(user_results['path'])
        global_count = len(user_results['novelty']) or len(user_results['coverage'])
        
        if prop_count:
            print(f"     • metricas_nivel_propiedad.csv  ~ {prop_count} filas")
        if example_count:
            print(f"     • metricas_nivel_ejemplo.csv    ~ {example_count} filas")
        if path_count:
            print(f"     • metricas_caminos.csv          ~ {path_count} filas")
        if global_count:
            print(f"     • metricas_globales.csv         ~ {global_count} filas")
    
    print(f"\n{'─'*80}")
    print()


if __name__ == "__main__":
    # Para testing: procesar solo 2 archivos
    # Descomenta la siguiente línea para modo test:
    # run_all_subgraphs(limit=2)
    
    # Para producción: procesar todos los archivos
    run_all_subgraphs()