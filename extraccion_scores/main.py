"""
Script principal para ejecutar el pipeline de métricas XAI
Sistema de Evaluación de Explicabilidad en Recomendaciones de Hoteles

Autor: Cristina
TFM MUSII
"""
from pathlib import Path
import sys
import argparse

from src.pipeline import XAICoveragePipeline


def configurar_argumentos():
    """
    Configura los argumentos de línea de comandos
    """
    parser = argparse.ArgumentParser(
        description='Pipeline de evaluación de cobertura XAI para sistemas de recomendación'
    )
    
    parser.add_argument(
        '--recomendaciones',
        type=str,
        default='data/recomendaciones.csv',
        help='Ruta al CSV con recomendaciones (user, hotel_recomendado)'
    )
    
    parser.add_argument(
        '--explicaciones',
        type=str,
        default='data/propiedades_compartidas.csv',
        help='Ruta al CSV con propiedades compartidas'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/resultados_metricas_cobertura.csv',
        help='Ruta de salida para los resultados'
    )
    
    parser.add_argument(
        '--analizar-usuario',
        type=int,
        default=None,
        help='ID de usuario específico para análisis detallado'
    )
    
    parser.add_argument(
        '--comparar-usuarios',
        type=str,
        default=None,
        help='IDs de usuarios a comparar, separados por comas (ej: 3,39,90)'
    )
    
    return parser.parse_args()


def main():
    """
    Función principal del pipeline
    """
    # Parsear argumentos
    args = configurar_argumentos()
    
    # Configuración de rutas
    BASE_DIR = Path(__file__).parent
    
    # Resolver rutas relativas
    if not Path(args.recomendaciones).is_absolute():
        recomendaciones_path = BASE_DIR / args.recomendaciones
    else:
        recomendaciones_path = Path(args.recomendaciones)
    
    if not Path(args.explicaciones).is_absolute():
        explicaciones_path = BASE_DIR / args.explicaciones
    else:
        explicaciones_path = Path(args.explicaciones)
    
    if not Path(args.output).is_absolute():
        output_path = BASE_DIR / args.output
    else:
        output_path = Path(args.output)
    
    # Validar que existan los archivos de entrada
    if not recomendaciones_path.exists():
        print(f"\n✗ ERROR: No se encontró el archivo de recomendaciones:")
        print(f"  {recomendaciones_path}")
        print(f"\nPor favor, asegúrate de que el archivo existe.")
        return None
    
    if not explicaciones_path.exists():
        print(f"\n✗ ERROR: No se encontró el archivo de explicaciones:")
        print(f"  {explicaciones_path}")
        print(f"\nPor favor, asegúrate de que el archivo existe.")
        return None
    
    # Crear el pipeline
    print("\n" + "="*70)
    print(" SISTEMA XAI - EVALUACIÓN DE EXPLICABILIDAD")
    print(" TFM MUSII - Cristina")
    print("="*70)
    
    pipeline = XAICoveragePipeline(
        recomendaciones_path=str(recomendaciones_path),
        explicaciones_path=str(explicaciones_path),
        output_path=str(output_path)
    )
    
    # Ejecutar pipeline completo
    try:
        df_resultados = pipeline.ejecutar()
                
        # Análisis adicionales según argumentos
        if args.analizar_usuario is not None:
            print("\n")
            pipeline.analizar_usuario_especifico(user_id=args.analizar_usuario)
        
        if args.comparar_usuarios is not None:
            user_ids = [int(uid.strip()) for uid in args.comparar_usuarios.split(',')]
            print("\n")
            pipeline.comparar_usuarios(user_ids=user_ids)
                
        return df_resultados
        
    except Exception as e:
        print("\n" + "="*70)
        print("✗ ERROR DURANTE LA EJECUCIÓN")
        print("="*70)
        print(f"\nError: {e}")
        print("\nDetalles del error:")
        import traceback
        traceback.print_exc()
        print("\n")
        return None


if __name__ == "__main__":
    resultados = main()
    
    # Salir con código apropiado
    sys.exit(0 if resultados is not None else 1)