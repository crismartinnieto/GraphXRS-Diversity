#!/usr/bin/env python3
"""
Script para cambiar el MODE entre 'muestra' y 'completo' en todos los archivos.

Uso:
    python cambiar_modo.py completo
    python cambiar_modo.py muestra

Este script cambiará automáticamente el MODE en todos los archivos .py
del proyecto que lo tengan definido.
"""
import sys
from pathlib import Path


def cambiar_modo(nuevo_modo):
    """Cambia el MODE en todos los scripts del proyecto."""
    if nuevo_modo not in ['muestra', 'completo']:
        print("❌ Error: modo debe ser 'muestra' o 'completo'")
        print("\nUso: python cambiar_modo.py [muestra|completo]")
        sys.exit(1)
    
    # Definir rutas de los scripts (relativas a este archivo)
    raiz = Path(__file__).parent
    scripts = [
        # Scripts principales
        raiz / "src/extraccion_explicaciones_conocimiento/crear_explicaciones.py",
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/main_user_subgraph.py",
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/extract_interaction_subgraphs.py",
        raiz / "src/extraccion_metricas_conjunto/xaigraph.py",
        
        # Módulos de métricas
        raiz / "src/extraccion_metricas_conocimiento/métricas.py",
        raiz / "src/extraccion_metricas_interaccion/métricas.py",
        
        # Utilidades de conocimiento
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/save_graph.py",
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/utils_interactions.py",
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/utils_knowledge.py",
        
        # Utilidades de interacción
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/save_graph.py",
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/utils_interaction_patterns.py",
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/utils_interactions_expanded.py"
    ]
    
    print("="*70)
    print(f"CAMBIANDO MODE A: {nuevo_modo.upper()}")
    print("="*70)
    
    actualizados = 0
    no_encontrados = 0
    errores = 0
    
    for script_path in scripts:
        ruta_relativa = script_path.relative_to(raiz)
        
        if not script_path.exists():
            print(f"⚠️  No encontrado: {ruta_relativa}")
            no_encontrados += 1
            continue
        
        try:
            # Leer contenido
            contenido = script_path.read_text(encoding='utf-8')
            
            # Verificar si tiene MODE definido
            if 'MODE = "muestra"' not in contenido and 'MODE = "completo"' not in contenido:
                print(f"⚠️  Sin MODE:      {ruta_relativa}")
                continue
            
            # Reemplazar MODE (ambas posibilidades)
            contenido_nuevo = contenido.replace(
                'MODE = "muestra"', 
                f'MODE = "{nuevo_modo}"'
            ).replace(
                'MODE = "completo"', 
                f'MODE = "{nuevo_modo}"'
            )
            
            # Solo guardar si hubo cambios
            if contenido != contenido_nuevo:
                script_path.write_text(contenido_nuevo, encoding='utf-8')
                print(f"✅ Actualizado:   {ruta_relativa}")
                actualizados += 1
            else:
                print(f"ℹ️  Sin cambios:   {ruta_relativa} (ya estaba en {nuevo_modo})")
            
        except Exception as e:
            print(f"❌ Error:         {ruta_relativa}")
            print(f"   Detalle: {e}")
            errores += 1
    
    # Resumen final
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"✅ Archivos actualizados:     {actualizados}")
    print(f"ℹ️  Archivos sin cambios:     {len(scripts) - actualizados - no_encontrados - errores}")
    print(f"⚠️  Archivos no encontrados:  {no_encontrados}")
    print(f"❌ Errores:                   {errores}")
    print(f"\n🎯 Modo configurado: {nuevo_modo.upper()}")
    print("="*70)


def mostrar_modo_actual():
    """Muestra el MODE actual en cada archivo."""
    raiz = Path(__file__).parent
    scripts = [
        # Scripts principales
        raiz / "src/extraccion_explicaciones_conocimiento/crear_explicaciones.py",
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/main_user_subgraph.py",
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/extract_interaction_subgraphs.py",
        raiz / "src/extraccion_metricas_conjunto/xaigraph.py",
        
        # Módulos de métricas
        raiz / "src/extraccion_metricas_conocimiento/métricas.py",
        raiz / "src/extraccion_metricas_interaccion/métricas.py",
        
        # Utilidades de conocimiento
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/save_graph.py",
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/utils_interactions.py",
        raiz / "src/extraccion_subgrafos/subgrafo_conocimiento/utils_knowledge.py",
        
        # Utilidades de interacción
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/save_graph.py",
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/utils_interaction_patterns.py",
        raiz / "src/extraccion_subgrafos/subgrafo_interaccion/utils_interactions_expanded.py"
    ]
    
    print("="*70)
    print("MODO ACTUAL EN CADA ARCHIVO")
    print("="*70)
    
    for script_path in scripts:
        ruta_relativa = script_path.relative_to(raiz)
        
        if not script_path.exists():
            print(f"⚠️  {ruta_relativa:<60} NO EXISTE")
            continue
        
        try:
            contenido = script_path.read_text(encoding='utf-8')
            
            if 'MODE = "muestra"' in contenido:
                print(f"📊 {str(ruta_relativa):<60} muestra")
            elif 'MODE = "completo"' in contenido:
                print(f"📊 {str(ruta_relativa):<60} completo")
            else:
                print(f"⚠️  {str(ruta_relativa):<60} SIN MODE")
                
        except Exception as e:
            print(f"❌ {str(ruta_relativa):<60} ERROR: {e}")
    
    print("="*70)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Sin argumentos: mostrar modo actual
        mostrar_modo_actual()
        print("\nUso: python cambiar_modo.py [muestra|completo|status]")
        print("  muestra  - Cambia a modo muestra (5 usuarios)")
        print("  completo - Cambia a modo completo (todos los usuarios)")
        print("  status   - Muestra el modo actual de cada archivo")
        
    elif len(sys.argv) == 2:
        if sys.argv[1] == 'status':
            mostrar_modo_actual()
        else:
            cambiar_modo(sys.argv[1])
    else:
        print("❌ Error: demasiados argumentos")
        print("\nUso: python cambiar_modo.py [muestra|completo|status]")
        sys.exit(1)