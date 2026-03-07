"""
docker/loader/load_databases.py
Carga los 3 grafos en Neo4j. Se ejecuta dentro del contenedor Docker.
Los CSVs se montan desde: NUEVA_ESTRUCTURA/data/raw/ → /data/ dentro del contenedor.
"""
import os
import sys
import time
import pandas as pd
from py2neo import Graph, SystemGraph
import logging

# ============================================================
# LOGGING → redirige también a fichero de log si está montado
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# CONEXIÓN NEO4J — via variables de entorno del docker-compose
# ============================================================
time.sleep(20)  # Esperar a que Neo4j arranque

uri      = os.getenv("NEO4J_URI",      "bolt://neo4j:7687")
user     = os.getenv("NEO4J_USER",     "neo4j")
password = os.getenv("NEO4J_PASSWORD", "test12345")

# Rutas de los CSVs dentro del contenedor (montados desde data/raw/)
DATA_DIR = "/data"
CSV_TRAIN        = f"{DATA_DIR}/grafo_interaccion_datos_train.csv"
CSV_HOTELES      = f"{DATA_DIR}/grafo_conocimiento_datos_hoteles.csv"

# ============================================================
# CREAR BASES DE DATOS
# ============================================================
logger.info("🔧 Conectando al sistema para crear bases de datos...")
system_graph = SystemGraph(uri, auth=(user, password))

for db_name in ["interactions", "knowledge"]:
    try:
        system_graph.run(f"CREATE DATABASE `{db_name}` IF NOT EXISTS")
        logger.info(f"✅ Base '{db_name}' creada/verificada")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo crear '{db_name}': {e}")

time.sleep(5)

# ============================================================
# CARGAR BASE 'interactions'
# ============================================================
logger.info("\n📦 === CARGANDO BASE 'interactions' ===")
graph_interactions = Graph(uri, auth=(user, password), name="interactions")
graph_interactions.run("MATCH (n) DETACH DELETE n")

logger.info(f"📂 Leyendo: {CSV_TRAIN}")
df_train = pd.read_csv(CSV_TRAIN)
logger.info(f"🔹 Filas: {len(df_train)}")

graph_interactions.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE;")
graph_interactions.run("CREATE CONSTRAINT business_id IF NOT EXISTS FOR (b:Business) REQUIRE b.id IS UNIQUE;")

records = [
    {"user_id": int(r["user_id"]), "business_id": int(r["business_id"]), "rating": float(r["rating"])}
    for _, r in df_train.iterrows()
]
graph_interactions.run("""
UNWIND $rows AS row
MERGE (u:User {id: row.user_id})
MERGE (b:Business {id: row.business_id})
MERGE (u)-[r:RATED]->(b)
SET r.rating = row.rating
""", rows=records)
logger.info(f"✅ 'interactions': {len(records)} relaciones insertadas")

# ============================================================
# CARGAR BASE 'knowledge'
# ============================================================
logger.info("\n📦 === CARGANDO BASE 'knowledge' ===")
graph_knowledge = Graph(uri, auth=(user, password), name="knowledge")
graph_knowledge.run("MATCH (n) DETACH DELETE n")

logger.info(f"📂 Leyendo: {CSV_HOTELES}")
df_hotels = pd.read_csv(CSV_HOTELES)
logger.info(f"🔹 Filas: {len(df_hotels)}")

graph_knowledge.run("CREATE CONSTRAINT business_id IF NOT EXISTS FOR (b:Business) REQUIRE b.id IS UNIQUE;")

records_knowledge = []
for _, row in df_hotels.iterrows():
    business = str(row['item_id'])
    records_knowledge.append({"src": business, "dst": row['name'],             "rel": "has_name"})
    records_knowledge.append({"src": business, "dst": row['city'],             "rel": "located_in_city"})
    records_knowledge.append({"src": business, "dst": row['state'],            "rel": "in_state"})
    records_knowledge.append({"src": business, "dst": str(row['postal_code']), "rel": "has_postal_code"})

    if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
        records_knowledge.append({"src": business, "dst": f"({row['latitude']:.4f}, {row['longitude']:.4f})", "rel": "has_coordinates"})
    if pd.notna(row.get('stars')):
        records_knowledge.append({"src": business, "dst": f"{row['stars']} stars", "rel": "has_rating"})
    if pd.notna(row.get('review_count')):
        records_knowledge.append({"src": business, "dst": f"{int(row['review_count'])} reviews", "rel": "has_review_count"})
    if pd.notna(row.get('is_open')):
        records_knowledge.append({"src": business, "dst": "open" if row['is_open'] == 1 else "closed", "rel": "status"})
    if isinstance(row.get('category'), str):
        for cat in [c.strip() for c in row['category'].split(',') if c.strip()]:
            records_knowledge.append({"src": business, "dst": cat, "rel": "has_category"})
    if pd.notna(row.get('attribute_key')) and pd.notna(row.get('attribute_value')):
        records_knowledge.append({"src": business, "dst": f"{row['attribute_key']}={row['attribute_value']}", "rel": "has_attribute"})

logger.info(f"🔗 Relaciones a insertar: {len(records_knowledge)}")
graph_knowledge.run("""
UNWIND $rows AS row
MERGE (b:Business {id: row.src})
MERGE (n:Node {name: row.dst})
MERGE (b)-[r:RELATION {type: row.rel}]->(n)
""", rows=records_knowledge)
logger.info(f"✅ 'knowledge': {len(records_knowledge)} relaciones insertadas")

# ============================================================
# RESUMEN FINAL
# ============================================================
logger.info("\n📊 === RESUMEN FINAL ===")
for nombre, g in [("interactions", graph_interactions), ("knowledge", graph_knowledge)]:
    logger.info(f"\n🔹 Base '{nombre}':")
    for row in g.run("MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS cantidad").data():
        logger.info(f"  {row['tipo']}: {row['cantidad']}")

logger.info("\n✅ Todas las bases de datos cargadas correctamente")