import pandas as pd
from functools import reduce

# ---------------------------------------
# 1. CARGAR TODOS LOS CSV
# ---------------------------------------

metrics_content      = pd.read_csv("metrics_content.csv")
metrics_coverage     = pd.read_csv("metrics_coverage.csv")
metrics_diversity    = pd.read_csv("metrics_diversity.csv")
metrics_examples     = pd.read_csv("metrics_examples.csv")
metrics_novelty      = pd.read_csv("metrics_novelty.csv")
metrics_path         = pd.read_csv("metrics_path.csv")
metrics_popularity   = pd.read_csv("metrics_popularity.csv")
metrics_recency      = pd.read_csv("metrics_recency.csv")
metrics_similarity   = pd.read_csv("metrics_similarity.csv")

# ---------------------------------------
# 2. DEFINIR LAS KEYS DE MERGE
# ---------------------------------------
# Notar que algunos CSV tienen "propiedad" y otros no.
# Usamos el merge más inclusivo posible.
KEYS_PROP = ["usuario", "hotel_recomendado", "propiedad"]
KEYS_NO_PROP = ["usuario", "hotel_recomendado"]

# ---------------------------------------
# 3. NORMALIZAR COLUMNAS, EVITAR DUPLICADOS
# ---------------------------------------

def normalize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df

dfs = [
    metrics_content, metrics_coverage, metrics_diversity,
    metrics_examples, metrics_novelty, metrics_path,
    metrics_popularity, metrics_recency, metrics_similarity
]

dfs = [normalize_columns(df) for df in dfs]

# ---------------------------------------
# 4. UNIR DATAFRAMES
# ---------------------------------------

# Primero unir métricas que SI tienen "propiedad"
dfs_prop = [df for df in dfs if "propiedad" in df.columns]
merged_prop = reduce(lambda left, right: pd.merge(
    left, right, on=KEYS_PROP, how="outer"), dfs_prop)

# Luego unir CSV que NO tienen la columna propiedad
dfs_no_prop = [df for df in dfs if "propiedad" not in df.columns]

merged_full = reduce(lambda left, right: pd.merge(
    left, right, on=KEYS_NO_PROP, how="outer"), [merged_prop] + dfs_no_prop)

# ---------------------------------------
# 5. ORDENAR COLUMNAS
# ---------------------------------------
main_cols = ["usuario", "hotel_recomendado", "hotel_consumido", "propiedad"]
other_cols = [c for c in merged_full.columns if c not in main_cols]
merged_full = merged_full[main_cols + other_cols]

# ---------------------------------------
# 6. GUARDAR RESULTADO FINAL
# ---------------------------------------
merged_full.to_csv("metrics_full_explanation.csv", index=False)

print("✓ metrics_full_explanation.csv generado correctamente")
