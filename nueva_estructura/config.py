from pathlib import Path
import os

# ============================================================
# RUTA BASE — ajusta según entorno
# ============================================================
# LOCAL Windows:
BASE_DIR = Path(r"C:\Users\cris\Desktop\MUSII\TFM\nueva_estructura")

# SERVIDOR (comenta la de arriba y descomenta esta):
# BASE_DIR = Path("/home/jupyter-crismartinnieto/nueva_estructura")

# ============================================================
# MODE: 'muestra' (5 usuarios, para pruebas) o 'completo'
# ============================================================
MODE = "muestra"

USUARIOS_MUESTRA = [3, 35, 276, 339, 376]

# ============================================================
# DATA — entradas
# ============================================================
DATA_DIR = BASE_DIR / "data"
RAW_DIR  = DATA_DIR / "raw"

CSV_INTERACCION_TRAIN       = RAW_DIR / "grafo_interaccion_datos_train.csv"
CSV_CONOCIMIENTO_HOTELES    = RAW_DIR / "grafo_conocimiento_datos_hoteles.csv"
CSV_INTERACCION_RECOMEND    = RAW_DIR / "grafo_interaccion_con_recomendaciones.csv"
CSV_USUARIO_RATING_RECOMEND = RAW_DIR / "relacion_usuario_rating_recomendador.csv"

# --- GRAFO DE CONOCIMIENTO ---
SUBGRAFOS_CONOCIMIENTO        = DATA_DIR / f"subgrafos_conocimiento_{MODE}"
EXPLICACIONES_HISTORICO       = DATA_DIR / f"explicaciones_historico_{MODE}"
EXPLICACIONES_HISTORICO_Y_REC = DATA_DIR / f"explicaciones_historico_y_recomendacion_{MODE}"

# --- GRAFO DE INTERACCION ---
SUBGRAFOS_INTERACCIONES = DATA_DIR / f"subgrafos_interacciones_{MODE}"

# ============================================================
# OUTPUT — salidas finales
# ============================================================
OUTPUT_DIR            = BASE_DIR / "output"
METRICAS_CONOCIMIENTO = OUTPUT_DIR / f"metricas_grafo_conocimiento_{MODE}"
METRICAS_INTERACCION  = OUTPUT_DIR / f"metricas_grafo_interaccion_{MODE}"

# ============================================================
# LOGS
# ============================================================
LOGS_DIR = BASE_DIR / "logs"

# ============================================================
# NEO4J
# ============================================================
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "test12345")

# ============================================================
# Crear carpetas al importar config
# ============================================================
for _dir in [
    RAW_DIR,
    SUBGRAFOS_CONOCIMIENTO,
    SUBGRAFOS_INTERACCIONES,
    EXPLICACIONES_HISTORICO,
    EXPLICACIONES_HISTORICO_Y_REC,
    METRICAS_CONOCIMIENTO,
    METRICAS_INTERACCION,
    LOGS_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)