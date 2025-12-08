"""
Runner principal para extraer todas las métricas de explicabilidad
"""
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List
import json
import traceback

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
        print("\n[1/11] Calculando métricas de caminos...")
        try:
            path_results = compute_all_path_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['path'] = convert_results_to_business_ids(subgraph, path_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['path'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['path'] = []
        
        # 2. Métricas de centralidad
        print("[2/11] Calculando métricas de centralidad...")
        try:
            centrality_results = compute_all_centrality_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids, amf_scores)
            results['centrality'] = convert_results_to_business_ids(subgraph, centrality_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['centrality'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['centrality'] = []
        
        # 3. Métricas de contenido/atributos
        print("[3/11] Calculando métricas de contenido...")
        try:
            content_results = compute_all_content_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['content'] = convert_results_to_business_ids(subgraph, content_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['content'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['content'] = []
        
        # 4. Métricas basadas en ejemplos
        print("[4/11] Calculando métricas de ejemplos...")
        try:
            examples_results = compute_all_example_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['examples'] = convert_results_to_business_ids(subgraph, examples_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['examples'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['examples'] = []
        
        # 5. Métricas de similitud
        print("[5/11] Calculando métricas de similitud...")
        try:
            similarity_results = compute_all_similarity_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['similarity'] = convert_results_to_business_ids(subgraph, similarity_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['similarity'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['similarity'] = []
        
        # 6. Métricas de popularidad
        print("[6/11] Calculando métricas de popularidad...")
        try:
            popularity_results = compute_all_popularity_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['popularity'] = convert_results_to_business_ids(subgraph, popularity_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['popularity'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['popularity'] = []
        
        # 7. Métricas de diversidad
        print("[7/11] Calculando métricas de diversidad...")
        try:
            diversity_results = compute_all_diversity_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['diversity'] = convert_results_to_business_ids(subgraph, diversity_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['diversity'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['diversity'] = []
        
        # 8. Métricas de novedad
        print("[8/11] Calculando métricas de novedad...")
        try:
            novelty_results = compute_all_novelty_metrics(subgraph, user_id, hotel_rec_node_id, consumed_hotels_node_ids)
            results['novelty'] = convert_results_to_business_ids(subgraph, novelty_results, hotel_id_from_file, consumed_mapping)
            print(f"      → {len(results['novelty'])} filas generadas")
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            traceback.print_exc()
            results['novelty'] = []
        
        # 9. Métricas de cobertura
        print("[9/11] Calculando métricas de cobertura...")
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

def save_metrics_to_csv(all_results: List[Dict], category: str, output_dir: str):
    """
    Guarda métricas de una categoría en CSV.
    """
    if not all_results:
        print(f"⚠️  No hay resultados para {category}")
        return
    
    try:
        df = pd.DataFrame(all_results)
        
        if df.empty:
            print(f"⚠️  DataFrame vacío para {category}")
            return
        
        output_path = os.path.join(output_dir, f"metrics_{category}.csv")
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"✓ Guardado: {output_path} ({len(df)} filas)")
        
    except Exception as e:
        print(f"❌ Error guardando {category}: {str(e)}")
        traceback.print_exc()

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
    
    # Acumuladores por categoría
    accumulated_results = {
        'path': [],
        'centrality': [],
        'content': [],
        'examples': [],
        'similarity': [],
        'popularity': [],
        'diversity': [],
        'novelty': [],
        'coverage': [],
        'recency': [],
        'type_relationship': []
    }
    
    # Estadísticas
    successful = 0
    failed = 0
    
    # Procesar cada subgrafo
    for i, filename in enumerate(subgraph_files, 1):
        filepath = os.path.join(SUBGRAPHS_DIR, filename)
        
        print(f"\n{'─'*80}")
        print(f"Progreso: {i}/{len(subgraph_files)} ({i/len(subgraph_files)*100:.1f}%)")
        
        try:
            results = process_single_subgraph(filepath)
            
            if results:
                # Acumular resultados
                for category, data in results.items():
                    accumulated_results[category].extend(data)
                successful += 1
            else:
                failed += 1
        
        except Exception as e:
            print(f"❌ ERROR INESPERADO procesando {filename}: {str(e)}")
            traceback.print_exc()
            failed += 1
            continue
    
    # Guardar todos los CSVs
    print(f"\n{'='*80}")
    print("GUARDANDO RESULTADOS EN CSV...")
    print(f"{'='*80}\n")
    
    for category, data in accumulated_results.items():
        save_metrics_to_csv(data, category, OUTPUT_DIR)
    
    print(f"\n{'#'*80}")
    print("# ✅ PROCESO COMPLETADO")
    print(f"{'#'*80}\n")
    
    # Resumen final
    print("RESUMEN DE PROCESAMIENTO:")
    print(f"{'─'*80}")
    print(f"  • Archivos procesados exitosamente: {successful}")
    print(f"  • Archivos con errores: {failed}")
    print(f"  • Total: {successful + failed}")
    print(f"{'─'*80}\n")
    
    print("RESUMEN DE MÉTRICAS GENERADAS:")
    print(f"{'─'*80}")
    for category, data in accumulated_results.items():
        print(f"  • {category:25s}: {len(data):6d} filas")
    print(f"{'─'*80}")
    total_rows = sum(len(data) for data in accumulated_results.values())
    print(f"  {'TOTAL':25s}: {total_rows:6d} filas")
    print()

if __name__ == "__main__":
    # Para testing: procesar solo 2 archivos
    # Descomenta la siguiente línea para modo test:
    #run_all_subgraphs(limit=2)
    
    # Para producción: procesar todos los archivos
    run_all_subgraphs()