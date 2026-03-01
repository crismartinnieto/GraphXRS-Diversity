"""
src/extraccion_metricas_conjunto/xaigraph.py

Módulo unificado LIMPIO para el cálculo de métricas XAI sobre grafos.
SOLO contiene lógica de coordinación compartida.
La lógica específica de cada tipo está en sus respectivos módulos.

Uso:
    from xaigraph import XAIGraphMetrics
    
    # Para métricas de conocimiento
    xai = XAIGraphMetrics(tipo='conocimiento')
    xai.calcular_y_guardar()
    
    # Para métricas de interacción
    xai = XAIGraphMetrics(tipo='interaccion')
    xai.calcular_y_guardar()

IMPORTANTE: Ejecutar siempre desde la raíz del proyecto:
    python src/extraccion_metricas_conjunto/xaigraph.py
"""
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Literal

import pandas as pd

# ============================================================
# MODE: 'muestra' o 'completo'
# ============================================================
MODE = "muestra"  # Cambiar a "completo" para procesar todos los usuarios
USUARIOS_MUESTRA = [3, 35, 276, 339, 376]  # Usuarios para modo muestra

# ============================================================
# RUTAS RELATIVAS AL DIRECTORIO DE TRABAJO (raíz del proyecto)
# Ejecutar siempre desde: Sistema_recomendacion_xai_TFM_MUSII_CMN/
# ============================================================
PROJECT_ROOT = Path(".")  # Directorio de trabajo = raíz del proyecto

DATA_DIR   = PROJECT_ROOT / "data"
RAW_DIR    = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR   = PROJECT_ROOT / "logs"

CSV_USUARIO_RATING_RECOMEND   = RAW_DIR / "relacion_usuario_rating_recomendador.csv"
EXPLICACIONES_HISTORICO_Y_REC = DATA_DIR / f"explicaciones_historico_y_recomendacion_{MODE}"
SUBGRAFOS_INTERACCIONES       = DATA_DIR / f"subgrafos_interacciones_{MODE}"
METRICAS_CONOCIMIENTO         = OUTPUT_DIR / f"metricas_grafo_conocimiento_{MODE}"
METRICAS_INTERACCION          = OUTPUT_DIR / f"metricas_grafo_interaccion_{MODE}"

# Crear carpetas si no existen
for _dir in [METRICAS_CONOCIMIENTO, METRICAS_INTERACCION, LOGS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# IMPORTS DE MÓDULOS ESPECÍFICOS
# Añadir src/ al path para poder importar los submódulos
# ============================================================
_src_dir = Path(__file__).parent.parent  # extraccion_metricas_conjunto/ → src/
sys.path.insert(0, str(_src_dir))

from extraccion_metricas_conocimiento.métricas import (
    CalculadorMetricas,
    PropiedadesCompartidasStrategy,
    RatioPropiedadesCompartidasStrategy,
    CoberturaTiposPropiedadesStrategy,
    PrecisionAtKStrategy,
    RecallAtKStrategy,
    F1AtKStrategy,
    NDCGStrategy,
    MRRStrategy,
    HitRateStrategy,
    MAPStrategy,
    DiversidadTiposStrategy,
    NovedadPropiedadesStrategy,
    SerendipiaStrategy,
    ConsistenciaTiposStrategy,
    PesoPonderadoPerfilStrategy,
    SimilaridadJaccardStrategy,
    BalanceTiposPropiedadesStrategy,
    RiquezaExplicativaStrategy,
)

from extraccion_metricas_interaccion.métricas import (
    CalculadorCentralidades,
    DegreeCentralidadHotelStrategy,
    RatioUsuariosCompartidosStrategy,
    NumUsuariosCompartidosStrategy,
    PesoMedioRatingHotelStrategy,
    NormDegreeCentralidadHotelStrategy,
)


# ============================================================
# CLASE PRINCIPAL UNIFICADA - SOLO COORDINACIÓN
# ============================================================

class XAIGraphMetrics:
    """
    Clase unificada para calcular métricas XAI sobre grafos.
    SOLO contiene lógica de coordinación compartida.
    Delega la lógica específica a los módulos correspondientes.
    """

    def __init__(self, tipo: Literal['conocimiento', 'interaccion'] = 'conocimiento'):
        self.tipo = tipo
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._setup_logging()

        if tipo == 'conocimiento':
            self.output_dir = METRICAS_CONOCIMIENTO
            self.prefijo = 'kg'
        else:
            self.output_dir = METRICAS_INTERACCION
            self.prefijo = 'cf'

        self.calculador = self._crear_calculador()
        self.estrategias = self._cargar_estrategias()
        self.calculador.agregar_estrategias(self.estrategias)

    def _setup_logging(self):
        log_file = f"metricas_{self.tipo}.log"
        self.logger = logging.getLogger(f"xaigraph.{self.tipo}")
        self.logger.setLevel(logging.INFO)
        if self.logger.handlers:
            self.logger.handlers.clear()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        fh = logging.FileHandler(LOGS_DIR / log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def _crear_calculador(self):
        if self.tipo == 'conocimiento':
            return CalculadorMetricas()
        else:
            return CalculadorCentralidades()

    def _cargar_estrategias(self) -> List:
        if self.tipo == 'conocimiento':
            return [
                PropiedadesCompartidasStrategy(),
                RatioPropiedadesCompartidasStrategy(),
                CoberturaTiposPropiedadesStrategy(),
                PrecisionAtKStrategy(k=5),
                RecallAtKStrategy(k=5),
                F1AtKStrategy(k=5),
                NDCGStrategy(k=5),
                MRRStrategy(),
                HitRateStrategy(),
                MAPStrategy(),
                DiversidadTiposStrategy(),
                NovedadPropiedadesStrategy(threshold=2),
                SerendipiaStrategy(),
                ConsistenciaTiposStrategy(),
                PesoPonderadoPerfilStrategy(),
                SimilaridadJaccardStrategy(),
                BalanceTiposPropiedadesStrategy(),
                RiquezaExplicativaStrategy(),
            ]
        else:
            return [
                DegreeCentralidadHotelStrategy(),
                RatioUsuariosCompartidosStrategy(),
                NumUsuariosCompartidosStrategy(),
                PesoMedioRatingHotelStrategy(),
                NormDegreeCentralidadHotelStrategy(),
            ]

    def _obtener_usuarios(self) -> List[int]:
        if not CSV_USUARIO_RATING_RECOMEND.exists():
            self.logger.error(f"❌ No existe: {CSV_USUARIO_RATING_RECOMEND}")
            sys.exit(1)

        df = pd.read_csv(CSV_USUARIO_RATING_RECOMEND)
        usuarios_todos = df['usuario'].unique()

        if self.tipo == 'conocimiento':
            usuarios = sorted([
                u for u in usuarios_todos
                if (EXPLICACIONES_HISTORICO_Y_REC /
                    f"explicaciones_usuario_{u}_hotel_his_y_rec.csv").exists()
            ])
            if not usuarios:
                self.logger.error(f"❌ Sin explicaciones en {EXPLICACIONES_HISTORICO_Y_REC}")
                self.logger.error("   Ejecuta primero crear_explicaciones.py")
                sys.exit(1)
        else:
            if MODE == "muestra":
                usuarios = [u for u in USUARIOS_MUESTRA if u in usuarios_todos]
            else:
                usuarios = [
                    u for u in usuarios_todos
                    if list(SUBGRAFOS_INTERACCIONES.glob(f"user_{u}_hotel_*_interactions.json"))
                ]
            if not usuarios:
                self.logger.error("❌ Sin usuarios con subgrafos. Ejecuta antes extract_interaction_subgraphs.py")
                sys.exit(1)

        return usuarios

    def _guardar_metrica(self, df_resultados: pd.DataFrame, usuario: int, nombre_metrica: str):
        if nombre_metrica not in df_resultados.columns:
            self.logger.warning(f"  ⚠️  Columna '{nombre_metrica}' no encontrada, se omite")
            return

        columnas_base = ['usuario', 'hotel_recomendado']
        col_hotel_compartido = None
        if 'hotel_historico' in df_resultados.columns:
            col_hotel_compartido = 'hotel_historico'
        elif 'hotel_compartido' in df_resultados.columns:
            col_hotel_compartido = 'hotel_compartido'
        else:
            self.logger.error("❌ No se encuentra columna de hotel compartido en resultados")
            return

        df_metrica = (
            df_resultados[columnas_base + [col_hotel_compartido, nombre_metrica]]
            .rename(columns={col_hotel_compartido: 'hotel_compartido', nombre_metrica: 'valor_metrica'})
        )

        nombre_fichero = f"{self.prefijo}_usuario_{usuario}_{nombre_metrica}_{self.timestamp}.csv"
        output_path = self.output_dir / nombre_fichero
        df_metrica.to_csv(output_path, index=False, encoding='utf-8')
        self.logger.info(f"  💾 {nombre_fichero}  ({len(df_metrica)} filas)")

    def _procesar_usuario(self, usuario: int) -> bool:
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Usuario {usuario}")
        self.logger.info(f"{'='*60}")

        try:
            resultados = self.calculador.calcular_para_usuario(usuario)
            df_resultados = pd.DataFrame(resultados)
            self.logger.info(f"  Combinaciones calculadas: {len(df_resultados)}")

            nombres_metricas = [e.nombre() for e in self.estrategias]
            for nombre_metrica in nombres_metricas:
                self._guardar_metrica(df_resultados, usuario, nombre_metrica)

            self.logger.info(f"✅ Usuario {usuario}: {len(nombres_metricas)} ficheros guardados")
            return True

        except FileNotFoundError as e:
            self.logger.error(f"❌ Ficheros no encontrados para usuario {usuario}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error en usuario {usuario}: {e}")
            import traceback
            traceback.print_exc()
            return False

    def calcular_y_guardar(self):
        self.logger.info("=" * 70)
        self.logger.info(f"CÁLCULO MÉTRICAS {self.tipo.upper()} — MODE={MODE}")
        self.logger.info(f"Timestamp: {self.timestamp}")
        self.logger.info("=" * 70)

        if self.tipo == 'conocimiento':
            self.logger.info(f"📂 Explicaciones his+rec: {EXPLICACIONES_HISTORICO_Y_REC}")
        else:
            self.logger.info(f"📂 Subgrafos: {SUBGRAFOS_INTERACCIONES}")

        self.logger.info(f"💾 Salida: {self.output_dir}")
        usuarios = self._obtener_usuarios()
        self.logger.info(f"\n👥 Usuarios a procesar: {len(usuarios)} → {usuarios}\n")

        nombres_metricas = [e.nombre() for e in self.estrategias]
        self.logger.info(f"📐 Métricas registradas ({len(nombres_metricas)}): {nombres_metricas}\n")

        exitos = 0
        for usuario in usuarios:
            if self._procesar_usuario(usuario):
                exitos += 1

        self.logger.info(f"\n{'='*70}")
        self.logger.info("🎉 COMPLETADO")
        self.logger.info(f"   Usuarios procesados:  {exitos}/{len(usuarios)}")
        self.logger.info(f"   Métricas:             {len(nombres_metricas)}")
        self.logger.info(f"   Ficheros generados:   {exitos * len(nombres_metricas)}")
        self.logger.info(f"   Resultados en:        {self.output_dir}")
        self.logger.info(f"{'='*70}")


# ============================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================

def calcular_metricas_conocimiento():
    """Atajo para calcular métricas del grafo de conocimiento."""
    xai = XAIGraphMetrics(tipo='conocimiento')
    xai.calcular_y_guardar()


def calcular_metricas_interaccion():
    """Atajo para calcular métricas del grafo de interacción."""
    xai = XAIGraphMetrics(tipo='interaccion')
    xai.calcular_y_guardar()


def calcular_todas_las_metricas():
    """Calcula tanto métricas de conocimiento como de interacción."""
    print("\n🚀 Calculando métricas de CONOCIMIENTO...")
    calcular_metricas_conocimiento()
    print("\n🚀 Calculando métricas de INTERACCIÓN...")
    calcular_metricas_interaccion()


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Calcula métricas XAI sobre grafos de conocimiento e interacción"
    )
    parser.add_argument(
        '--tipo',
        choices=['conocimiento', 'interaccion', 'todas'],
        default='todas',
        help='Tipo de métricas a calcular (default: todas)'
    )
    args = parser.parse_args()

    if args.tipo == 'conocimiento':
        calcular_metricas_conocimiento()
    elif args.tipo == 'interaccion':
        calcular_metricas_interaccion()
    else:
        calcular_todas_las_metricas()


if __name__ == "__main__":
    main()