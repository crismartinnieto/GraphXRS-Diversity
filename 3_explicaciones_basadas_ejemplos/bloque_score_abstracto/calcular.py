from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter
import ast
from typing import Dict, List, Any

from métricas import *


# ============================================================================
# FUNCIÓN PRINCIPAL REFACTORIZADA
# ============================================================================

def main():
    """Función principal que usa el patrón Strategy"""
    
    # ===== CONFIGURACIÓN DE RUTAS =====
    # Este script está en: 3_explicaciones_basadas_ejemplos/bloque_score_abstracto/
    script_dir = Path(__file__).resolve().parent
    print(f"\n📁 Directorio del script: {script_dir}")
    
    # Subir 2 niveles para llegar a la raíz del proyecto
    project_root = script_dir.parent.parent
    print(f"📁 Raíz del proyecto: {project_root}")
    
    # Directorio de datos de recomendaciones (INPUT)
    recomend_dir = project_root / 'data_recommender'
    print(f"📂 Directorio de recomendaciones: {recomend_dir}")
    
    # Directorio de salida (OUTPUT)
    # En: 3_explicaciones_basadas_ejemplos/resultados_scores/
    output_dir = script_dir.parent / 'resultados_scores'
    print(f"💾 Directorio de salida: {output_dir}")
    
    # ===== VERIFICACIÓN DE DIRECTORIOS =====
    if not recomend_dir.exists():
        print(f"\n❌ ERROR: No existe el directorio de recomendaciones: {recomend_dir}")
        print("   Verifica la estructura del proyecto.")
        return
    
    recomend_file = recomend_dir / 'relacion_usuario_rating_recomendador.csv'
    if not recomend_file.exists():
        print(f"\n❌ ERROR: No existe el archivo: {recomend_file}")
        return
    
    # Crear directorio de salida si no existe
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Directorio de salida creado/verificado\n")
    
    # ===== CARGAR DATOS =====
    print("="*80)
    print("CARGANDO DATOS")
    print("="*80)

    print(f"\n📊 Cargando recomendaciones desde: {recomend_file.name}")
    df_recomend = pd.read_csv(recomend_file)
    print(f"   ✓ Registros cargados: {len(df_recomend)}")

    # Obtener usuarios únicos del CSV de recomendaciones
    usuarios_recomend = df_recomend['usuario'].unique()
    print(f"   ℹ️ Usuarios en recomendaciones: {len(usuarios_recomend)}")

    # NUEVO: Filtrar solo usuarios que tienen explicaciones
    explicaciones_dir = script_dir.parent / 'explicaciones_basadas_ejemplos' / 'data'
    usuarios_con_explicaciones = []

    for usuario in usuarios_recomend:
        archivo_comparacion = explicaciones_dir / f'explicaciones_usuario_{usuario}_hotel_his_y_rec.csv'
        if archivo_comparacion.exists():
            usuarios_con_explicaciones.append(usuario)

    usuarios = sorted(usuarios_con_explicaciones)
    print(f"   ✓ Usuarios con explicaciones: {len(usuarios)}")
    print(f"   👥 IDs de usuarios: {usuarios}\n")

    if len(usuarios) == 0:
        print(f"\n❌ ERROR: No se encontraron usuarios con explicaciones en {explicaciones_dir}")
        return
    
    # Configurar calculador con todas las estrategias
    calculador = CalculadorMetricas()
    
    # Agregar métricas de cobertura
    calculador.agregar_estrategias([
        PropiedadesCompartidasStrategy(),
        RatioPropiedadesCompartidasStrategy(),
        CoberturaTiposPropiedadesStrategy()
    ])
    
    # Agregar métricas de ranking
    calculador.agregar_estrategias([
        PrecisionAtKStrategy(k=5),
        RecallAtKStrategy(k=5),
        F1AtKStrategy(k=5),
        NDCGStrategy(k=5),
        MRRStrategy(),
        HitRateStrategy(),
        MAPStrategy()
    ])
    
    # Agregar métricas de diversidad y novedad
    calculador.agregar_estrategias([
        DiversidadTiposStrategy(),
        NovedadPropiedadesStrategy(threshold=2),
        SerendipiaStrategy()
    ])
    
    # Agregar métricas de consistencia y fidelidad
    calculador.agregar_estrategias([
        ConsistenciaTiposStrategy(),
        PesoPonderadoPerfilStrategy(),
        SimilaridadJaccardStrategy()
    ])
    
    # Agregar métricas de balance y distribución
    calculador.agregar_estrategias([
        BalanceTiposPropiedadesStrategy(),
        RiquezaExplicativaStrategy()
    ])
    
    # Procesar cada usuario
    for usuario in usuarios:
        print(f"{'='*70}")
        print(f"Procesando Usuario {usuario}")
        print(f"{'='*70}\n")
        
        try:
            # Calcular todas las métricas
            resultados = calculador.calcular_para_usuario(usuario)
            
            # Convertir a DataFrame
            df_resultados = pd.DataFrame(resultados)
            
            # Guardar archivo
            output_file = output_dir / f'metricas_completas_usuario_{usuario}.csv'
            df_resultados.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"  ✓ Métricas guardadas: {output_file.name}")
            print(f"    Filas: {len(df_resultados)}, Columnas: {len(df_resultados.columns)}")
            print(f"    Métricas calculadas: {len(calculador.estrategias)}\n")
            
            print(f"{'='*70}")
            print(f"✅ Usuario {usuario} procesado correctamente")
            print(f"{'='*70}\n")
            
        except FileNotFoundError as e:
            print(f"  ✗ Error: No se encontraron archivos para usuario {usuario}")
            print(f"    {str(e)}\n")
            
        except Exception as e:
            print(f"  ✗ Error procesando usuario {usuario}: {str(e)}\n")
            import traceback
            traceback.print_exc()
    
    # Resumen final
    print(f"\n{'='*70}")
    print("🎉 PROCESO COMPLETADO")
    print(f"{'='*70}")
    print(f"Total de usuarios procesados: {len(usuarios)}")
    print(f"Total de métricas por combinación: {len(calculador.estrategias)}")
    print(f"Directorio de salida: {output_dir}")


if __name__ == "__main__":
    main()