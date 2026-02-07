import os
import time
import pandas as pd
from py2neo import Graph, SystemGraph
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

time.sleep(20)

uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "test12345")

# ==========================================
# CREAR BASES DE DATOS
# ==========================================
logger.info("🔧 Conectando al sistema para crear bases de datos...")
system_graph = SystemGraph(uri, auth=(user, password))

# Crear base 'interactions' si no existe
try:
    system_graph.run("CREATE DATABASE interactions IF NOT EXISTS")
    logger.info("✅ Base 'interactions' creada/verificada")
except Exception as e:
    logger.warning(f"⚠️ No se pudo crear 'interactions': {e}")

# Crear base 'knowledge' si no existe
try:
    system_graph.run("CREATE DATABASE knowledge IF NOT EXISTS")
    logger.info("✅ Base 'knowledge' creada/verificada")
except Exception as e:
    logger.warning(f"⚠️ No se pudo crear 'knowledge': {e}")

time.sleep(5)  # Esperar a que las bases estén listas

# ==========================================
# CARGAR BASE 'interactions'
# ==========================================
logger.info("\n📦 === CARGANDO BASE 'interactions' ===")
graph_interactions = Graph(uri, auth=(user, password), name="interactions")

logger.info("🧹 Limpiando base 'interactions'...")
graph_interactions.run("MATCH (n) DETACH DELETE n")

logger.info("📂 Cargando datos de interacción desde TRAIN...")
df_train = pd.read_csv("/data/grafo_interaccion_datos_train.csv")

logger.info(f"🔹 Filas cargadas: {len(df_train)}")

# Crear constraints
graph_interactions.run("""
CREATE CONSTRAINT user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;
""")

graph_interactions.run("""
CREATE CONSTRAINT business_id IF NOT EXISTS
FOR (b:Business) REQUIRE b.id IS UNIQUE;
""")

# Preparar registros
records = [
    {
        "user_id": int(row["user_id"]),
        "business_id": int(row["business_id"]),
        "rating": float(row["rating"])
    }
    for _, row in df_train.iterrows()
]

query = """
UNWIND $rows AS row
MERGE (u:User {id: row.user_id})
MERGE (b:Business {id: row.business_id})
MERGE (u)-[r:RATED]->(b)
SET r.rating = row.rating
"""

logger.info("🚀 Insertando relaciones...")
graph_interactions.run(query, rows=records)

logger.info(f"✅ 'interactions': {len(records)} relaciones insertadas")

# ==========================================
# CARGAR BASE 'knowledge'
# ==========================================
logger.info("\n📦 === CARGANDO BASE 'knowledge' ===")
graph_knowledge = Graph(uri, auth=(user, password), name="knowledge")

logger.info("🧹 Limpiando base 'knowledge'...")
graph_knowledge.run("MATCH (n) DETACH DELETE n")

logger.info("📂 Cargando grafo de conocimiento...")
df_hotels = pd.read_csv("/data/grafo_conocimiento_datos_hoteles.csv")

logger.info(f"🔹 Filas cargadas: {len(df_hotels)}")

graph_knowledge.run("CREATE CONSTRAINT business_id IF NOT EXISTS FOR (b:Business) REQUIRE b.id IS UNIQUE;")

records_knowledge = []
for _, row in df_hotels.iterrows():
    business = str(row['item_id'])
    
    records_knowledge.append({"src": business, "dst": row['name'], "rel": "has_name"})
    records_knowledge.append({"src": business, "dst": row['city'], "rel": "located_in_city"})
    records_knowledge.append({"src": business, "dst": row['state'], "rel": "in_state"})
    records_knowledge.append({"src": business, "dst": str(row['postal_code']), "rel": "has_postal_code"})
    
    if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
        coord = f"({row['latitude']:.4f}, {row['longitude']:.4f})"
        records_knowledge.append({"src": business, "dst": coord, "rel": "has_coordinates"})
    
    if pd.notna(row.get('stars')):
        records_knowledge.append({"src": business, "dst": f"{row['stars']} stars", "rel": "has_rating"})
    
    if pd.notna(row.get('review_count')):
        records_knowledge.append({"src": business, "dst": f"{int(row['review_count'])} reviews", "rel": "has_review_count"})
    
    if pd.notna(row.get('is_open')):
        status = "open" if row['is_open'] == 1 else "closed"
        records_knowledge.append({"src": business, "dst": status, "rel": "status"})
    
    if isinstance(row.get('category'), str):
        for cat in [c.strip() for c in row['category'].split(',') if c.strip()]:
            records_knowledge.append({"src": business, "dst": cat, "rel": "has_category"})
    
    if pd.notna(row.get('attribute_key')) and pd.notna(row.get('attribute_value')):
        attr_label = f"{row['attribute_key']}={row['attribute_value']}"
        records_knowledge.append({"src": business, "dst": attr_label, "rel": "has_attribute"})

logger.info(f"🔗 Total de relaciones a insertar: {len(records_knowledge)}")

query_knowledge = """
UNWIND $rows AS row
MERGE (b:Business {id: row.src})
MERGE (n:Node {name: row.dst})
MERGE (b)-[r:RELATION {type: row.rel}]->(n)
"""
graph_knowledge.run(query_knowledge, rows=records_knowledge)
logger.info(f"✅ 'knowledge': {len(records_knowledge)} relaciones insertadas")

# ==========================================
# RESUMEN FINAL
# ==========================================
logger.info("\n📊 === RESUMEN FINAL ===")

logger.info("\n🔹 Base 'interactions':")
result_int = graph_interactions.run("MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS cantidad").data()
for row in result_int:
    logger.info(f"  {row['tipo']}: {row['cantidad']}")

logger.info("\n🔹 Base 'knowledge':")
result_know = graph_knowledge.run("MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS cantidad").data()
for row in result_know:
    logger.info(f"  {row['tipo']}: {row['cantidad']}")

logger.info("\n✅ Ambas bases de datos cargadas correctamente")