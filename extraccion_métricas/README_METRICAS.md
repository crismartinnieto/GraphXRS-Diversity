# Métricas para Explicabilidad en el Sistema de Recomendación (Knowledge Graph)

Este proyecto utiliza un *Knowledge Graph (KG)* para generar explicaciones sobre las recomendaciones de hoteles.
Para evaluar la calidad de estas explicaciones, se implementan métricas:

* **Métricas basadas en caminos** → archivo: `metrics_path.py`
* **Métricas basadas en centralidad** → archivo: `metrics_centrality.py`
* **Métricas basadas en contenido** → archivo: `metrics_content.py`
* **Métricas basadas en ejemplos** → archivo: `metrics_examples.py`
* **Métricas basadas en similitud** → archivo: `metrics_similarity.py`
* **Métricas basadas en popularidad** → archivo: `metrics_popularity.py`
* **Métricas basadas en novedad** → archivo: `metrics_novelty.py`
* **Métricas basadas en cobertura** → archivo: `metrics_coverage.py`
* **Métricas basadas en centralidad** → archivo: `metrics_centrality.py`
* **Métricas basadas en recency** → archivo: `metrics_recency.py`
* **Métricas basadas en tipo de relación** → archivo: `metrics_type_relationship.py`


A continuación se describen de forma sencilla todas las métricas implementadas.

---

## Métricas Basadas en Caminos (`metrics_path.py`)

Estas métricas analizan los **caminos** que conectan el hotel consumido por el usuario con el hotel recomendado dentro del Knowledge Graph. Evalúan qué tan clara, robusta o variada es la explicación.

### **1. Path Length**

Cantidad de saltos que hay entre el hotel consumido y el hotel recomendado.

Las explicaciones más cortas suelen ser más fáciles de entender.

### **2. Path Count**

Número total de caminos distintos que justifican la recomendación.

Más caminos = mayor robustez en la explicación.

### **3. Shared-Property Weight Score**

Se asigna un peso a cada tipo de propiedad compartida (ejemplo: ubicación, categoría, amenidades).

La puntuación final es la suma de los pesos de todas las propiedades comunes.

### **4. Path Type Variety**

Número de tipos de relaciones diferentes que aparecen entre ambos hoteles (ej.: `has_category`, `located_in_city`, `has_attribute`).

Más variedad = explicaciones más completas.

### **5. Path Type Frequency**

Para cada tipo de relación, se cuenta cuántos hoteles comparten ese tipo con el recomendado.
Sirve para medir cuán común es ese tipo de explicación.

### **6. Path Confidence Score**

Cada tipo de relación tiene un peso (ej.: ubicación=3, categoría=2, atributos=1).
La puntuación es la suma de los pesos de los tipos compartidos.
Mide qué tan “fuerte” es la explicación basada en propiedades relevantes.

### **7. Weighted Knowledge Path Score**

Definición: peso × cantidad de valores por cada tipo de relación.
Mide la fuerza total acumulada de todos los caminos explicativos entre dos hoteles, ponderada por la importancia de cada tipo de relación.

### CSV OBTENIDO

| Columna | Tipo | Descripción | Interpretación del valor |
|--------|------|-------------|---------------------------|
| **usuario** | Identificador | ID del usuario al que pertenece la explicación. | No es métrica. Solo identifica al usuario. |
| **hotel_recomendado** | Identificador | ID del hotel recomendado. | No es métrica. |
| **hotel_consumido** | Identificador | ID de un hotel consumido por el usuario. | No es métrica. |
| **propiedad** | Propiedad compartida | Propiedad específica compartida entre el consumido y el recomendado (ej.: `has_category:Tours`). | Cada fila corresponde a una propiedad concreta que justifica la recomendación. |
| **path_length** | Métrica | Longitud del camino más corto entre ambos hoteles. | **Menor es mejor.** 2 = comparten propiedad; ∞ = no hay conexión. |
| **path_count** | Métrica | Número total de propiedades compartidas entre los hoteles. | **Mayor es mejor.** Más conexiones ⇒ mayor robustez. |
| **path_type_variety** | Métrica | Número de tipos de relación distintos compartidos. | **Mayor es mejor.** Más variedad ⇒ explicación más completa. |
| **shared_property_weight_score** | Métrica | Suma de los pesos de todas las propiedades compartidas, considerando cantidad. | **Mayor es mejor.** Captura fuerza total basada en cantidad + importancia. |
| **path_confidence_score** | Métrica | Suma de pesos de los tipos de relación compartidos (sin contar cantidad). | **Mayor es mejor.** Evalúa relevancia de tipos compartidos. |
| **weighted_kps** | Métrica | Weighted Knowledge Path Score: suma total de (peso × cantidad) por cada tipo de relación. | **Mayor es mejor.** Refleja la fuerza explicativa global. |
| **path_type_frequency** | Métrica descriptiva | Número de hoteles consumidos que comparten el tipo de relación de esta fila con el recomendado. | **No es “mejor/peor”**. Alto = tipo común; bajo = tipo más específico/personalizado. |

---

## Métricas Basadas en Centralidad (`metrics_centrality.py`)

Estas métricas analizan la **importancia estructural** de los atributos dentro del Knowledge Graph.
Evalúan si una explicación se basa en propiedades que realmente son relevantes o influyentes dentro del grafo.

### **1. Degree Centrality**

Número de hoteles conectados a un atributo.

Atributos populares = explicaciones más universales.

### **2. Normalized Degree Centrality**

El grado se normaliza entre 0 y 1.

Permite comparar atributos en grafos de distinto tamaño.

### **3. Betweenness Centrality**

Mide cuántas veces un atributo actúa como “puente” entre hoteles.

Útil para detectar atributos clave, aunque en grafos pequeños suele ser baja.

### **4. Closeness Centrality**

Evalúa qué tan cerca está un atributo del resto del grafo.

Atributos más cercanos → más relevantes para el sistema.

### **5. Eigenvector Centrality**

Mide si un atributo está conectado con otros atributos también importantes. Es decir, qué tan conectado está el atributo con otros atributos centrales.

Indica influencia estructural.

### **6. PageRank**

Versión más estable de centralidad basada en enlaces.

### **7. Harmonic Centrality**

Similar a closeness, pero más robusta cuando no hay conexiones directas.
Suma los inversos de las distancias.

### **8. Attribute Influence Score**

Combina la centralidad con su capacidad de diferenciación (AMF).
Mide cuánta influencia real tiene una propiedad al explicar recomendaciones.

### CSV OBTENIDO

| Columna | Tipo | Descripción | Interpretación del valor |
|--------|------|-------------|---------------------------|
| **usuario** | Identificador | ID del usuario al que pertenece la explicación. | No es métrica. Solo identifica al usuario. |
| **hotel_recomendado** | Identificador | ID del hotel recomendado. | No es métrica. |
| **propiedad** | Propiedad del recomendado | Atributo del hotel recomendado que se está evaluando (ej.: `has_attribute:GoodForKids=True`). | No es métrica; describe la propiedad analizada. |
| **hotel_consumido** | Identificador | Hotel consumido que comparte esta propiedad (si existe). | No es métrica. `NaN` = ningún hotel consumido comparte este atributo. |
| **degree_centrality** | Métrica estructural | Número de nodos conectados a esta propiedad. Mide popularidad del atributo. | **Mayor es mejor.** Indica atributo común en el grafo. |
| **normalized_degree_centrality** | Métrica estructural | Versión normalizada del grado (0–1). | **Mayor es mejor.** Atributo más frecuente en proporción al tamaño del grafo. |
| **betweenness_centrality** | Métrica estructural | Mide si la propiedad actúa como puente entre comunidades del grafo. | **Mayor es mejor.** Atributo estructuralmente más relevante. |
| **closeness_centrality** | Métrica estructural | Indica la cercanía del atributo al resto del grafo según distancias. | **Mayor es mejor.** Atributo más “accesible” en la red. |
| **eigenvector_centrality** | Métrica estructural | Mide importancia del atributo considerando la importancia de sus vecinos. | **Mayor es mejor.** Atributo conectado con nodos influyentes. |
| **pagerank** | Métrica estructural | Mide relevancia basándose en flujos de probabilidad (PageRank). | **Mayor es mejor.** Atributo estructuralmente destacado. |
| **harmonic_centrality** | Métrica estructural | Variante del closeness que suma inversos de distancias. | **Mayor es mejor.** Evita problemas en grafos desconectados. |
| **attribute_influence_score** | Métrica | Score final que mide la influencia de la propiedad (Degree × factor de coincidencia). | **Mayor es mejor.** Indica cuánto aporta esta propiedad a justificar la recomendación. |

---

# Métricas Basadas en Contenido/Atributos (`metrics_content.py`)

Estas métricas analizan directamente los **atributos** del hotel recomendado y cómo se relacionan con los atributos de los hoteles consumidos por el usuario.

### **1. Attribute Match Frequency (AMF)**

Indica qué proporción de los hoteles consumidos tiene un atributo presente en el recomendado. 

Mide afinidad directa entre gustos del usuario y atributos del ítem.

### **2. Attribute Frequency (TF_user)**

Número de veces que el usuario ha consumido un atributo específico.  

Atributos frecuentes → representan bien el perfil del usuario.
    
### **3. Attribute TF-IDF (Discriminative Feature Score)**

Destaca atributos frecuentes en los consumidos por el usuario pero raros en el catálogo general.  

Sirve para identificar preferencias “únicas”.

### **4. Attribute Contribution Score**

Cuantifica cuánto contribuye un atributo específico a justificar la recomendación.
Es la combinación entre frecuencia del atributo en los consumos y presencia en el recomendado.

### **5. Attribute Presence Ratio (APR)**

Proporción de atributos del recomendado que el usuario ya ha consumido antes.

### **6. Attribute Overlap Count**

Número total de atributos compartidos entre hotel recomendado y consumidos.

### **7. Attribute Novelty**

Detecta si un atributo es nuevo para el usuario.

1 = nuevo, 0 = ya conocido.

### **8. Attribute Specificity (Inverse Popularity)**

Qué tan raro es un atributo en el catálogo.

Menos popular = más explicativo. 

### **9. Attribute Stability**

Qué tan constante es un atributo en el histórico del usuario.

Atributos estables = preferencias firmes.

### **10. Attribute Variability**

Qué tan variable es un atributo en los consumidos; baja variabilidad indica gusto representativo del usuario.

Baja variabilidad = atributo representativo del usuario.

---

# Métricas Basadas en Ejemplos (`metrics_examples.py`)

Estas métricas comparan el recomendado con los hoteles consumidos para generar explicaciones basadas en ejemplos.

### **1. Example Similarity Score**

Similitud entre el recomendado y un hotel consumido.

### **2. Most Similar Consumed Example**

Hotel consumido más parecido al recomendado. 

### **3. Least Similar Consumed Example (Contrastive)**

Hotel consumido menos parecido.  

Útil para explicaciones contrastivas, tipo “por qué este y no aquel”.

### **4. Mean Example Similarity**

Similitud promedio entre el recomendado y todos los consumidos. 

### **5. k-Nearest Example Strength**

Suma de similitudes de los k consumidos más parecidos.  

### **6. Example Support Score (por atributo)**

Número de consumidos que tienen un atributo del recomendado.

### **7. Relative Example Strength**

Normalización del soporte por el total de consumidos.

### **8. Example Density**

Frecuencia de un atributo entre todos los atributos consumidos. 

### **9. Example Coverage**

Porcentaje de consumidos que comparten al menos un atributo con el recomendado.  

### **10. Example Consensus Score**

Homogeneidad de los ejemplos que respaldan la recomendación.

### **11. Example Disagreement Score**

Variabilidad en la similitud entre consumidos y recomendado.

### **12. Prototype Example Score**

Selecciona el ejemplo más representativo del usuario (centroide).
Luego compara su similitud con el recomendado.

---

# Métricas de Similitud (`metrics_similarity.py`)

Evaluan la similitud entre consumidos y recomendado a nivel de atributos o vectores.

### **1. Jaccard Similarity**

Similitud binaria entre los atributos de consumido y recomendado.  

### **2. Cosine Similarity**

Similitud vectorial entre representaciones de atributos.

### **3. Shared Attribute Count**

Conteo absoluto de atributos compartidos. 

### **4. Weighted Shared Attribute Score**

Conteo ponderado según la importancia de cada atributo.  

### **5. Shared Category Count**

Conteo específico de categorías compartidas.

### **6. Shared Location Count**

Coincidencias de ubicación (ciudad, país, región…).

### **7. Category Alignment Score**

Proporción de categorías del recomendado que coinciden con las del usuario.

### **8. Path Count (Graph)**

Cantidad de caminos en el KG entre consumido y recomendado.

### **9. Path Length (Graph)**

Distancia más corta o promedio en el KG.

### **10. Weighted Knowledge Path Score (KPS)**

Suma de pesos de todos los caminos relevantes.

---

# Métricas de Popularidad (`metrics_popularity.py`)

Evalúan lo comunes o raros que son los atributos.

### **1. Attribute Popularity**

Número de hoteles conectados al atributo.

### **2. Attribute Popularity Rank**

Percentil del atributo respecto al catálogo.

### **3. Inverse Popularity**

Atributos menos populares → más interesantes.

### **4. Commonality Score**

Cuántos usuarios han consumido ese atributo.
Requiere histórico de interacción.

---

# Métricas de Diversidad (`metrics_diversity.py`)

### **1. Explanation Type Diversity**

Número de tipos de relación usados en las explicaciones.

### **2. Attribute Diversity del recomendado**

Número de tipos de atributos presentes en el ítem recomendado.

### **3. Cross-Explanation Diversity**

Diversidad entre explicaciones generadas para un mismo usuario.

---

# Métricas de Recencia (`metrics_recency.py`)

### **1. Recency Score**

Da más peso a interacciones recientes.

### **2. Normalized Recency Rank**

Normaliza la recencia respecto al historial completo.

---

# Métricas de Novedad/Serendipia (`metrics_novelty.py`)

### **1. Novelty Count**

Número de atributos nuevos del recomendado.

### **2. Novelty Ratio**

Porcentaje de atributos nuevos del recomendado.

### **3. Surprise Score**

Novedad × rareza (inversa de popularidad).
Modelo típico de “sorpresa”.

---

# Métricas de Cobertura de Preferencias (`metrics_coverage.py`)

### **1. Preference Coverage**

Proporción de preferencias del usuario cubiertas por el recomendado.

### **2. Blind-Spot Coverage**

Información nueva aportada:
1 – Coverage.

---

# Métricas por Tipo de Relación (`metrics_type_relationship.py`)

### **1. Type-Specific Match Frequency**

Coincidencias específicas según tipo:

* CityMatch
* CategoryMatch
* AmenityMatch

### **2. Weighted Type Match Score**

Combina los tipos anteriores con pesos.


---

# 📘 Tabla Resumen de Métricas

| Métrica (función Python)                     | Tipo        | Descripción breve                                                   | Archivo                        |
| ------------------------------------------   | ----------- | ------------------------------------------------------------------  | -----------------------------  |
| **path_length**                              | Camino      | Saltos entre hotel consumido y recomendado.                         | `metrics_path.py`              |
| **path_count**                               | Camino      | Número de caminos explicativos.                                     | `metrics_path.py`              |
| **shared_property_weight_score**             | Camino      | Suma de pesos de propiedades compartidas.                           | `metrics_path.py`              |
| **path_type_variety**                        | Camino      | Número de tipos de relación compartidos.                            | `metrics_path.py`              |
| **path_type_frequency**                      | Camino      | Frecuencia de cada tipo de relación entre hoteles.                  | `metrics_path.py`              |
| **path_confidence_score**                    | Camino      | Suma de pesos de tipos de relación.                                 | `metrics_path.py`              |
| **weighted_knowledge_path_score**            | Camino      | Suma de pesos de todos los caminos relevantes.                      | `metrics_path.py`              |
| **compute_degree_centrality**                | Centralidad | Cantidad de conexiones del atributo.                                | `metrics_centrality.py`        |
| **compute_normalized_degree_centrality**     | Centralidad | Grado normalizado entre 0 y 1.                                      | `metrics_centrality.py`        |
| **compute_betweenness_centrality**           | Centralidad | Atributo como puente en el grafo.                                   | `metrics_centrality.py`        |
| **compute_closeness_centrality**             | Centralidad | Proximidad del atributo al resto.                                   | `metrics_centrality.py`        |
| **compute_eigenvector_centrality**           | Centralidad | Importancia según conexiones con otros nodos importantes.           | `metrics_centrality.py`        |
| **compute_pagerank**                         | Centralidad | Popularidad del atributo según enlaces.                             | `metrics_centrality.py`        |
| **compute_harmonic_centrality**              | Centralidad | Suma de 1/distancia con otros nodos.                                | `metrics_centrality.py`        |
| **compute_attribute_influence_score**        | Centralidad | Influencia combinada: centralidad × AMF.                            | `metrics_centrality.py`        |
| **preference_coverage**                      | Cobertura   | Cobertura del perfil del usuario                                    | `metrics_coverage.py`          |
| **blind_spot_coverage**                      | Cobertura   | Información nueva aportada                                          | `metrics_coverage.py`          |
| **attribute_match_frequency**                | Contenido   | Proporción de consumidos que tienen el atributo recomendado         | `metrics_content.py`           |
| **attribute_frequency**                      | Contenido   | Frecuencia absoluta del atributo en consumidos                      | `metrics_content.py`           |
| **attribute_tfidf**                          | Contenido   | Destaca atributos frecuentes en el usuario y raros en catálogo      | `metrics_content.py`           |
| **attribute_contribution_score**             | Contenido   | Relevancia del atributo para justificar la recomendación            | `metrics_content.py`           |
| **attribute_presence_ratio**                 | Contenido   | Proporción de atributos del recomendado que el usuario ya consumió  | `metrics_content.py`           |
| **attribute_overlap_count**                  | Contenido   | Número de atributos compartidos                                     | `metrics_content.py`           |
| **attribute_novelty**                        | Contenido   | Indica si un atributo es nuevo para el usuario                      | `metrics_content.py`           |
| **attribute_specificity**                    | Contenido   | Qué tan raro es el atributo en el catálogo                          | `metrics_content.py`           |
| **attribute_stability**                      | Contenido   | Constancia del atributo en el histórico del usuario                 | `metrics_content.py`           |
| **attribute_variability**                    | Contenido   | Qué tan variable es un atributo en los consumidos                   | `metrics_content.py`           |
| **explanation_type_diversity**               | Diversidad  | Variedad de tipos de relación en la explicación                     | `metrics_diversity.py`         |
| **attribute_diversity_recommended**          | Diversidad  | Variedad de atributos del hotel recomendado                         | `metrics_diversity.py`         |
| **cross_explanation_diversity**              | Diversidad  | Variedad de explicaciones generadas                                 | `metrics_diversity.py`         |
| **example_similarity_score**                 | Ejemplos    | Similitud recomendado-consumido                                     | `metrics_examples.py`          |
| **most_similar_consumed_example**            | Ejemplos    | Consumido más parecido al recomendado                               | `metrics_examples.py`          |
| **least_similar_consumed_example**           | Ejemplos    | Consumido menos parecido                                            | `metrics_examples.py`          |
| **mean_example_similarity**                  | Ejemplos    | Promedio de similitud                                               | `metrics_examples.py`          |
| **k_nearest_example_strength**               | Ejemplos    | Suma de similitudes de los k consumidos más cercanos                | `metrics_examples.py`          |
| **example_support_score**                    | Ejemplos    | Número de consumidos que tienen un atributo                         | `metrics_examples.py`          |
| **relative_example_strength**                | Ejemplos    | Soporte normalizado por total de consumidos                         | `metrics_examples.py`          |
| **example_density**                          | Ejemplos    | Frecuencia del atributo entre todos los consumidos                  | `metrics_examples.py`          |
| **example_coverage**                         | Ejemplos    | Porcentaje de consumidos que comparten atributos                    | `metrics_examples.py`          |
| **example_consensus_score**                  | Ejemplos    | Homogeneidad de los ejemplos de soporte                             | `metrics_examples.py`          |
| **example_disagreement_score**               | Ejemplos    | Variabilidad en similitud de ejemplos                               | `metrics_examples.py`          |
| **prototype_example_score**                  | Ejemplos    | Ejemplo más representativo y similitud con recomendado              | `metrics_examples.py`          |
| **novelty_count**                            | Novedad     | Número de atributos nuevos                                          | `metrics_novelty.py`           |
| **novelty_ratio**                            | Novedad     | Proporción de atributos nuevos                                      | `metrics_novelty.py`           |
| **surprise_score**                           | Novedad     | Novedad × InversePopularity                                         | `metrics_novelty.py`           |
| **attribute_popularity**                     | Popularidad | Número de hoteles conectados al atributo                            | `metrics_popularity.py`        |
| **attribute_popularity_rank**                | Popularidad | Percentil del atributo                                              | `metrics_popularity.py`        |
| **inverse_popularity**                       | Popularidad | Rareza / Unexpectedness del atributo                                | `metrics_popularity.py`        |
| **commonality_score**                        | Popularidad | Número de usuarios que consumieron el atributo                      | `metrics_popularity.py`        |
| **recency_score**                            | Recencia    | 1 / (1 + Δt)                                                        | `metrics_recency.py`           |
| **normalized_recency_rank**                  | Recencia    | Δt normalizado por el máximo                                        | `metrics_recency.py`           |
| **type_specific_match_frequency**            | Relaciones  | Coincidencias por tipo de relación                                  | `metrics_type_match.py`        |
| **weighted_type_match_score**                | Relaciones  | Suma ponderada de coincidencias                                     | `metrics_type_match.py`        |
| **jaccard_similarity_metric**                | Similitud   | Similitud binaria de atributos                                      | `metrics_similarity.py`        |
| **cosine_similarity_metric**                 | Similitud   | Similitud vectorizada de atributos                                  | `metrics_similarity.py`        |
| **shared_attribute_count**                   | Similitud   | Conteo absoluto de atributos compartidos                            | `metrics_similarity.py`        |
| **weighted_shared_attribute_score**          | Similitud   | Conteo ponderado por importancia                                    | `metrics_similarity.py`        |
| **shared_category_count**                    | Similitud   | Categorías compartidas                                              | `metrics_similarity.py`        |
| **shared_location_count**                    | Similitud   | Ubicaciones compartidas                                             | `metrics_similarity.py`        |
| **category_alignment_score**                 | Similitud   | Alineación de categorías con el usuario                             | `metrics_similarity.py`        |
| **path_count_graph**                         | Similitud   | Número de caminos en grafo                                          | `metrics_similarity.py`        |
| **path_length_graph**                        | Similitud   | Longitud de caminos                                                 | `metrics_similarity.py`        |
| **weighted_knowledge_path_score_similarity** | Similitud   | Suma ponderada de caminos en grafo                                  | `metrics_similarity.py`        |




