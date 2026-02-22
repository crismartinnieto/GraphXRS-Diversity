from pathlib import Path
import os

# ============================================================
# RUTA BASE — ajusta según entorno
# ============================================================
# LOCAL Windows (descomenta si trabajas en local):
# BASE_DIR = Path(r"C:\Users\cris\Desktop\MUSII\TFM\NUEVA_ESTRUCTURA")

# SERVIDOR (activo por defecto):
BASE_DIR = Path("/home/jupyter-crismartinnieto/NUEVA_ESTRUCTURA")

# ============================================================
# MODE: 'muestra' (5 usuarios, para pruebas) o 'completo'
# ============================================================
MODE = "muestra"  # ← cambia a "completo" cuando quieras ejecutar todo

# Usuarios de muestra (solo se usan cuando MODE = "muestra")
USUARIOS_MUESTRA = [3, 35, 276, 100, 200]

# ============================================================
# DATA — entradas
# ============================================================
DATA_DIR = BASE_DIR / "data"
RAW_DIR  = DATA_DIR / "raw"

# CSVs originales de entrada
CSV_INTERACCION_TRAIN       = RAW_DIR / "grafo_interaccion_datos_train.csv"
CSV_CONOCIMIENTO_HOTELES    = RAW_DIR / "grafo_conocimiento_datos_hoteles.csv"
CSV_INTERACCION_RECOMEND    = RAW_DIR / "grafo_interaccion_con_recomendaciones.csv"
CSV_USUARIO_RATING_RECOMEND = RAW_DIR / "relacion_usuario_rating_recomendador.csv"

# Subgrafos de conocimiento (JSONs generados por extraccion_subgrafos)
SUBGRAFOS_CONOCIMIENTO = DATA_DIR / f"subgrafos_conocimiento_{MODE}"

# Explicaciones (CSVs intermedios generados por extraccion_explicaciones_conocimiento)
EXPLICACIONES_HISTORICO       = DATA_DIR / f"explicaciones_historico_{MODE}"
EXPLICACIONES_HISTORICO_Y_REC = DATA_DIR / f"explicaciones_historico_y_recomendacion_{MODE}"

# ============================================================
# OUTPUT — salidas finales
# ============================================================
OUTPUT_DIR            = BASE_DIR / "output"
METRICAS_CONOCIMIENTO = OUTPUT_DIR / f"metricas_grafo_conocimiento_{MODE}"

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
# Crear carpetas necesarias al importar config
# ============================================================
for _dir in [
    RAW_DIR,
    SUBGRAFOS_CONOCIMIENTO,
    EXPLICACIONES_HISTORICO,
    EXPLICACIONES_HISTORICO_Y_REC,
    METRICAS_CONOCIMIENTO,
    LOGS_DIR,
]:
    _dir.mkdir(parents=True, exist_ok=True)