#!/bin/bash
# =============================================================================
# run.sh — Pipeline completo del Sistema de Recomendación XAI
# Uso:
#   ./run.sh              → ejecuta todo en modo definido en config.py
#   ./run.sh muestra      → fuerza modo muestra
#   ./run.sh completo     → fuerza modo completo
# =============================================================================

set -e  # Parar si cualquier comando falla

# ============================================================
# CONFIGURACIÓN
# ============================================================
BASE_DIR="/home/jupyter-crismartinnieto/NUEVA_ESTRUCTURA"
SRC="$BASE_DIR/src"
DOCKER="$BASE_DIR/docker"
LOGS="$BASE_DIR/logs"
PYTHON="python3"

# Si se pasa argumento, sobreescribir MODE en config.py temporalmente
if [ "$1" == "muestra" ] || [ "$1" == "completo" ]; then
    MODE_ARG=$1
    echo "⚙️  Forzando MODE=$MODE_ARG en config.py..."
    sed -i "s/^MODE = .*/MODE = \"$MODE_ARG\"/" "$SRC/config.py"
fi

mkdir -p "$LOGS"

echo ""
echo "=================================================================="
echo "  SISTEMA RECOMENDACIÓN XAI — $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================================="

# ============================================================
# PASO 1 — Docker: levantar Neo4j y cargar bases de datos
# ============================================================
echo ""
echo ">>> [1/4] Levantando Neo4j y cargando bases de datos..."
cd "$DOCKER"
docker-compose up -d neo4j
echo "    Esperando 30s a que Neo4j esté listo..."
sleep 30
docker-compose up neo4j-loader
echo "    ✅ Bases de datos cargadas. Ver: $LOGS/loader.log"
cd "$BASE_DIR"

# ============================================================
# PASO 2 — Extracción de subgrafos de conocimiento
# ============================================================
echo ""
echo ">>> [2/4] Extrayendo subgrafos de conocimiento..."
cd "$SRC/extraccion_subgrafos"
$PYTHON main_user_subgraph.py 2>&1 | tee -a "$LOGS/extraccion_subgrafos.log"
echo "    ✅ Subgrafos generados. Ver: $LOGS/extraccion_subgrafos.log"
cd "$BASE_DIR"

# ============================================================
# PASO 3 — Generación de explicaciones
# ============================================================
echo ""
echo ">>> [3/4] Generando explicaciones..."
cd "$SRC/extraccion_explicaciones_conocimiento"
$PYTHON crear_explicaciones.py 2>&1 | tee -a "$LOGS/explicaciones.log"
echo "    ✅ Explicaciones generadas. Ver: $LOGS/explicaciones.log"
cd "$BASE_DIR"

# ============================================================
# PASO 4 — Cálculo de métricas
# ============================================================
echo ""
echo ">>> [4/4] Calculando métricas..."
cd "$SRC/extraccion_metricas_conocimiento"
$PYTHON calcular.py 2>&1 | tee -a "$LOGS/metricas.log"
echo "    ✅ Métricas calculadas. Ver: $LOGS/metricas.log"
cd "$BASE_DIR"

# ============================================================
# RESUMEN
# ============================================================
echo ""
echo "=================================================================="
echo "  ✅ PIPELINE COMPLETADO — $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================================="
echo ""
echo "  📂 Subgrafos:     $BASE_DIR/data/subgrafos_conocimiento_*"
echo "  📂 Explicaciones: $BASE_DIR/data/explicaciones_*"
echo "  📂 Métricas:      $BASE_DIR/output/metricas_grafo_conocimiento_*"
echo "  📋 Logs:          $LOGS/"
echo ""