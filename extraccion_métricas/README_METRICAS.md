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
| **hotel_consumido** | Identificador | Hotel consumido que comparte esta propiedad (si existe). | No es métrica. `NaN` = ningún hotel consumido comparte este atributo porque estas métricas NO dependen de las comparaciones entre un hotel consumido y uno recomendado. Las centralidades se calculan solo sobre el grafo completo, NO sobre pares consumido–recomendado |
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

### **7. Attribute Overlap Ratio**

Overlap/Jaccard entre atributos del usuario y del recomendado.

### **8. Attribute Novelty**

Detecta si un atributo es nuevo para el usuario.

1 = nuevo, 0 = ya conocido.

### **9. Attribute Specificity (Inverse Popularity)**

Qué tan raro es un atributo en el catálogo.

Menos popular = más explicativo. 

### **10. Attribute Stability**

Qué tan constante es un atributo en el histórico del usuario.

Atributos estables = preferencias firmes.

### **11. Attribute Variability**

Qué tan variable es un atributo en los consumidos; baja variabilidad indica gusto representativo del usuario.

Baja variabilidad = atributo representativo del usuario.

### CSV OBTENIDO
| Columna                          | Tipo          | Descripción                                                                                          | Interpretación del valor                                                                             |
| -------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **usuario**                      | Identificador | ID del usuario al que pertenece la explicación.                                                      | No es métrica. Solo identifica al usuario.                                                           |
| **hotel_recomendado**            | Identificador | ID del hotel recomendado.                                                                            | No es métrica.                                                                                       |
| **hotel_consumido**              | Identificador | ID de un hotel consumido por el usuario.                                                             | Siempre `NaN` para métricas de contenido, porque se calculan a nivel de atributo global del usuario. |
| **propiedad**                    | Propiedad     | Propiedad específica del hotel recomendado (ej.: `has_category:Tours`).                              | Cada fila corresponde a un atributo concreto del hotel recomendado.                                  |
| **amf**                          | Métrica       | Attribute Match Frequency: proporción de hoteles consumidos por el usuario que tienen este atributo. | **Mayor es mejor.** 1 = todos los consumidos tienen el atributo; 0 = ninguno.                        |
| **attribute_frequency**          | Métrica       | Número de veces que el usuario ha consumido este atributo (TF).                                      | **Mayor es mejor.** Indica relevancia para el perfil del usuario.                                    |
| **attribute_tfidf**              | Métrica       | TF × IDF: resalta atributos frecuentes en el usuario pero raros en el catálogo.                      | **Mayor es mejor.** Atributo más discriminativo del perfil del usuario.                              |
| **attribute_contribution_score** | Métrica       | Contribución del atributo a la explicación: frecuencia en consumidos × presencia en recomendado.     | **Mayor es mejor.** Evalúa cuánto este atributo justifica la recomendación.                          |
| **attribute_presence_ratio**     | Métrica       | Proporción de atributos del recomendado que el usuario ya ha consumido (APR).                        | **Mayor es mejor.** 1 = usuario ya ha visto todos; 0 = ninguno.                                      |
| **attribute_overlap_count**      | Métrica       | Número total de atributos compartidos entre recomendado y consumidos.                                | **Mayor es mejor.** Más atributos compartidos ⇒ explicación más fuerte.                              |
| **attribute_overlap_ratio**      | Métrica       | Overlap/Jaccard entre atributos del usuario y del recomendado.                                       | **Mayor es mejor.** 1 = todos los atributos coinciden; 0 = ninguno.                                  |
| **attribute_novelty**            | Métrica       | Indica si el atributo es nuevo para el usuario.                                                      | 1 = nuevo; 0 = ya conocido.                                                                          |
| **attribute_specificity**        | Métrica       | Inversa de popularidad del atributo en el catálogo.                                                  | **Mayor es mejor.** Más raro ⇒ más explicativo.                                                      |
| **attribute_stability**          | Métrica       | Qué tan constante es el atributo en los consumos del usuario.                                        | **Mayor es mejor.** 1 = completamente estable; 0 = nunca repetido.                                   |
| **attribute_variability**        | Métrica       | Qué tan variable es este tipo de atributo en los consumidos.                                         | **Menor es mejor** para representatividad. 0 = siempre igual; 1 = muy variable.                      |

---

# Métricas Basadas en Ejemplos (`metrics_examples.py`)

Estas métricas comparan el recomendado con los hoteles consumidos para generar explicaciones basadas en ejemplos.

### **1. Example Similarity Score**

Similitud Jaccard entre el consumido y el recomendado.

### **2. Most Similar Consumed Example**

Flag que indica si este consumido es el más similar 

### **3. Least Similar Consumed Example (Contrastive)**

Flag que indica si este consumido es el menos similar.

Útil para explicaciones contrastivas, tipo “por qué este y no aquel”.

### **4. Mean Example Similarity**

Similitud promedio entre el recomendado y todos los consumidos. 

### **5. k-Nearest Example Strength**

Suma de similitudes de los k consumidos más parecidos.  

### **6. Example Density**

Frecuencia de un atributo entre todos los atributos consumidos. 

### **7. Example Coverage**

Porcentaje de consumidos que comparten al menos un atributo con el recomendado.  

### **8. Example Consensus Score**

Homogeneidad de los ejemplos que respaldan la recomendación.

### **9. Example Disagreement Score**

Variabilidad en la similitud entre consumidos y recomendado.

### **10. Prototype Example Score**

Selecciona el ejemplo más representativo del usuario (centroide).
Luego compara su similitud con el recomendado.

### CSV OBTENIDO
| Columna                        | Tipo                 | Descripción                                                                     | Interpretación del valor                                                                 |
| ------------------------------ | -------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **usuario**                    | Identificador        | ID del usuario al que pertenece la explicación.                                 | No es métrica. Solo identifica al usuario.                                               |
| **hotel_recomendado**          | Identificador        | ID del hotel recomendado.                                                       | No es métrica.                                                                           |
| **hotel_consumido**            | Identificador        | ID del hotel consumido por el usuario.                                          | No es métrica, pero sirve para comparar con el recomendado.                              |
| **propiedad**                  | Propiedad compartida | Propiedad específica (si aplica) del recomendado que se compara con consumidos. | Puede ser `None` si la métrica no es por propiedad.                                      |
| **example_similarity_score**   | Métrica              | Similitud Jaccard entre un hotel consumido y el recomendado.                    | **Mayor es mejor.** 1 = idénticos, 0 = sin coincidencias.                                |
| **mean_example_similarity**    | Métrica global       | Promedio de similitud entre el recomendado y todos los consumidos.              | **Mayor es mejor.** Refleja afinidad general del recomendado con el perfil del usuario.  |
| **k_nearest_example_strength** | Métrica global       | Suma de similitudes de los k consumidos más parecidos.                          | **Mayor es mejor.** Indica fuerza de los ejemplos más cercanos.                          |
| **example_coverage**           | Métrica global       | Porcentaje de consumidos que comparten al menos un atributo con el recomendado. | **Mayor es mejor.** 1 = todos los consumidos tienen al menos un atributo común.          |
| **example_consensus_score**    | Métrica global       | Promedio de atributos compartidos por cada ejemplo consumido.                   | **Mayor es mejor.** Indica consistencia de los ejemplos que respaldan la recomendación.  |
| **example_disagreement_score** | Métrica global       | Varianza de similitudes entre consumidos y recomendado.                         | **Menor es mejor.** Valores altos indican variabilidad; bajo = consenso fuerte.          |
| **is_most_similar**            | Flag                 | Indica si el consumido es el más similar al recomendado.                        | 1 = sí, 0 = no.                                                                          |
| **is_least_similar**           | Flag                 | Indica si el consumido es el menos similar (para explicaciones contrastivas).   | 1 = sí, 0 = no.                                                                          |
| **prototype_similarity**       | Métrica              | Similitud del prototipo del usuario con el recomendado.                         | **Mayor es mejor.** Refleja cuán representativo es el prototipo respecto al recomendado. |

---

# Métricas de Similitud (`metrics_similarity.py`)

Evaluan la similitud entre consumidos y recomendado a nivel de atributos o vectores.

### **1. Cosine Similarity**

Similitud vectorial entre representaciones de atributos.

### **2. Shared Attribute Count**

Conteo absoluto de atributos compartidos. 

### **3. Shared Category Count**

Conteo específico de categorías compartidas.

### **4. Shared Location Count**

Coincidencias de ubicación (ciudad, país, región…).

### **5. Category Alignment Score**

Proporción de categorías del recomendado que coinciden con las del usuario.

### **6. Path Count (Graph)**

Cantidad de caminos en el KG entre consumido y recomendado.

### **7. Path Length (Graph)**

Distancia más corta o promedio en el KG.

### **8. Weighted Knowledge Path Score (KPS)**

Suma de pesos de todos los caminos relevantes.

### **CSV OBTENIDO**
| Columna                             | Tipo                 | Descripción                                                                 | Interpretación del valor                                                |
| ----------------------------------- | -------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **usuario**                         | Identificador        | ID del usuario al que pertenece la explicación.                             | No es métrica. Solo identifica al usuario.                              |
| **hotel_recomendado**               | Identificador        | ID del hotel recomendado.                                                   | No es métrica.                                                          |
| **hotel_consumido**                 | Identificador        | ID del hotel consumido por el usuario.                                      | No es métrica.                                                          |
| **propiedad**                       | Propiedad compartida | Propiedad asociada a la métrica (opcional, normalmente `None`).             | Puede usarse para vincular métricas a un atributo específico.           |
| **cosine_similarity**               | Métrica              | Similitud vectorial (coseno) entre representaciones de atributos.           | **Mayor es mejor.** 1 = idénticos; 0 = ortogonales.                     |
| **shared_attribute_count**          | Métrica              | Número absoluto de atributos compartidos.                                   | **Mayor es mejor.** Más atributos compartidos → más parecido.           |
| **shared_category_count**           | Métrica              | Número de categorías compartidas (`has_category`).                          | **Mayor es mejor.** Indica alineación semántica.                        |
| **shared_location_count**           | Métrica              | Número de coincidencias de ubicación (ciudad, estado, postal).              | **Mayor es mejor.** Localización geográfica común.                      |
| **category_alignment_score**        | Métrica              | Proporción de categorías del recomendado que coinciden con las del usuario. | **Mayor es mejor.** 1 = todas las categorías alineadas; 0 = ninguna.    |
| **path_count**                      | Métrica              | Número de caminos entre consumido y recomendado en el KG.                   | **Mayor es mejor.** Más caminos = más relaciones compartidas.           |
| **path_length**                     | Métrica              | Longitud del camino más corto en el KG.                                     | **Menor es mejor.** 2 = comparten atributo; ∞ = sin conexión.           |
| **weighted_kps**                    | Métrica              | Suma ponderada de todos los caminos relevantes (Knowledge Path Score).      | **Mayor es mejor.** Refleja fuerza total de las conexiones en el grafo. |

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

### **CSV OBTENIDO**
| Columna                       | Tipo                | Descripción                                                                                        | Interpretación del valor                                              |
| ----------------------------- | ------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| **usuario**                   | Identificador       | ID del usuario al que pertenece la recomendación.                                                  | No es métrica. Solo identifica al usuario.                            |
| **hotel_recomendado**         | Identificador       | ID del hotel recomendado.                                                                          | No es métrica.                                                        |
| **propiedad**                 | Propiedad del hotel | Atributo específico del hotel recomendado (ej.: `has_attribute:GoodForKids=True`).                 | Cada fila corresponde a una propiedad concreta del recomendado.       |
| **hotel_consumido**           | Identificador       | Siempre `NaN` en estas métricas (no dependen de un hotel consumido).                               | No es métrica.                                                        |
| **attribute_popularity**      | Métrica             | Número de hoteles del catálogo que poseen este atributo.                                           | **Menor es mejor** si se busca rareza; mayor = atributo común.        |
| **attribute_popularity_rank** | Métrica             | Percentil del atributo respecto a todos los atributos del catálogo.                                | **Mayor = más raro** (atributo más exclusivo), **menor = más común**. |
| **inverse_popularity**        | Métrica             | 1 / Popularidad, destaca atributos raros.                                                          | **Mayor = más raro/interesante**, **menor = más común**.              |
| **commonality_score**         | Métrica             | Número de usuarios que han consumido este atributo (requiere historial completo; placeholder = 0). | **Mayor = más usado**, **menor = menos usado**.                       |

---

# Métricas de Diversidad (`metrics_diversity.py`)

### **1. Explanation Type Diversity**

Número de tipos de relación usados en las explicaciones.

### **2. Attribute Diversity del recomendado**

Número de tipos de atributos presentes en el ítem recomendado.

### **3. Cross-Explanation Diversity**

Diversidad entre explicaciones generadas para un mismo usuario.

### **CSV OBTENIDO**
| Columna                             | Tipo                | Descripción                                                                                 | Interpretación del valor                                                       |
| ----------------------------------- | ------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **usuario**                         | Identificador       | ID del usuario al que pertenece la recomendación.                                           | No es métrica. Solo identifica al usuario.                                     |
| **hotel_recomendado**               | Identificador       | ID del hotel recomendado.                                                                   | No es métrica.                                                                 |
| **hotel_consumido**                 | Identificador       | ID del hotel previamente consumido por el usuario.                                          | Se usa para calcular explicaciones y diversidad respecto al recomendado.       |
| **propiedad**                       | Propiedad del hotel | Atributo específico del hotel recomendado (ej.: `has_attribute:GoodForKids=True`).          | Actualmente `NaN` porque tus métricas no dependen de propiedades individuales. |
| **explanation_type_diversity**      | Métrica             | Número de tipos de relaciones compartidas entre el hotel consumido y el recomendado.        | **Mayor = más diversa la explicación**, más tipos de relaciones usadas.        |
| **attribute_diversity_recommended** | Métrica             | Número de tipos de atributos presentes en el hotel recomendado.                             | **Mayor = hotel recomendado más diverso en atributos**.                        |
| **cross_explanation_diversity**     | Métrica             | Promedio de `explanation_type_diversity` entre todos los hoteles consumidos por el usuario. | **Mayor = usuario recibe explicaciones más variadas para sus consumos**.       |

---

# Métricas de Novedad/Serendipia (`metrics_novelty.py`)

### **1. Novelty Count**

Número de atributos nuevos del recomendado.

### **2. Novelty Ratio**

Porcentaje de atributos nuevos del recomendado.

### **3. Surprise Score**

Novedad × rareza (inversa de popularidad).
Modelo típico de “sorpresa”.

### **CSV OBTENIDO**
| Columna               | Tipo                | Descripción                                                                          | Interpretación del valor                                                    |
| --------------------- | ------------------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| **usuario**           | Identificador       | ID del usuario al que pertenece la recomendación.                                    | No es métrica. Solo identifica al usuario.                                  |
| **hotel_recomendado** | Identificador       | ID del hotel recomendado.                                                            | No es métrica.                                                              |
| **hotel_consumido**   | Identificador       | Siempre `NaN` en estas métricas (no dependen de un hotel consumido).                 | No es métrica.                                                              |
| **propiedad**         | Propiedad del hotel | Siempre `NaN` en estas métricas (no dependen de propiedades individuales).           | No es métrica.                                                              |
| **novelty_count**     | Métrica             | Número de atributos del hotel recomendado que el usuario **no ha visto antes**.      | **Mayor = más atributos nuevos**, más novedoso para el usuario.             |
| **novelty_ratio**     | Métrica             | Proporción de atributos nuevos respecto al total de atributos del hotel recomendado. | Normaliza `novelty_count` según tamaño del hotel. **Mayor = más novedoso**. |
| **surprise_score**    | Métrica             | Combina novedad con rareza (inversa de popularidad). Modelo de “sorpresa”.           | **Mayor = hotel sorprendente**: atributos nuevos y poco comunes.            |

---

# Métricas de Cobertura de Preferencias (`metrics_coverage.py`)

### **1. Preference Coverage**

Proporción de preferencias del usuario cubiertas por el recomendado.

### **2. Blind-Spot Coverage**

Información nueva aportada:
1 – Coverage.

### **CSV OBTENIDO**
| Columna                 | Tipo                | Descripción                                                                                          | Interpretación del valor                                                    |
| ----------------------- | ------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **usuario**             | Identificador       | ID del usuario al que pertenece la recomendación.                                                    | No es métrica. Solo identifica al usuario.                                  |
| **hotel_recomendado**   | Identificador       | ID del hotel recomendado.                                                                            | No es métrica.                                                              |
| **hotel_consumido**     | Identificador       | Siempre `NaN` en estas métricas.                                                                     | No es métrica.                                                              |
| **propiedad**           | Propiedad del hotel | Siempre `NaN` en estas métricas.                                                                     | No es métrica.                                                              |
| **preference_coverage** | Métrica             | Proporción de atributos previamente consumidos por el usuario que están presentes en el recomendado. | **Mayor = el hotel satisface mejor las preferencias conocidas del usuario** |
| **blind_spot_coverage** | Métrica             | Complemento de `preference_coverage`. Indica la información nueva aportada por el recomendado.       | **Mayor = más información nueva**, el hotel es más exploratorio.            |

---

# Métricas por Tipo de Relación (`metrics_type_relationship.py`)

### **1. Type-Specific Match Frequency**

Coincidencias específicas según tipo:

* CityMatch
* CategoryMatch
* AmenityMatch

### **2. Weighted Type Match Score**

Combina los tipos anteriores con pesos.

### CSV OBTENIDO
| Columna                           | Tipo                | Descripción                                                                                 | Interpretación del valor                                                                                                            |
| --------------------------------- | ------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **usuario**                       | Identificador       | ID del usuario al que pertenece la recomendación.                                           | No es métrica. Solo identifica al usuario.                                                                                          |
| **hotel_recomendado**             | Identificador       | ID del hotel recomendado.                                                                   | No es métrica.                                                                                                                      |
| **hotel_consumido**               | Identificador       | Siempre `NaN` en estas métricas.                                                            | No es métrica.                                                                                                                      |
| **propiedad**                     | Propiedad del hotel | Siempre `NaN` en estas métricas.                                                            | No es métrica.                                                                                                                      |
| **relation_type**                 | Tipo de relación    | Tipo específico de relación analizada (ej.: `CityMatch`, `CategoryMatch`, `AmenityMatch`).  | Se usa para calcular la frecuencia de coincidencia y el score ponderado.                                                            |
| **semantic_group**                | Grupo semántico     | Categoría semántica a la que pertenece el tipo de relación (ej.: `identity`, `attribute`).  | Ayuda a agrupar tipos similares.                                                                                                    |
| **type_specific_match_frequency** | Métrica             | Frecuencia de coincidencia para el tipo de relación entre hoteles consumidos y recomendado. | **Mayor = más coincidencias** entre el recomendado y el historial del usuario.                                                      |
| **relation_weight**               | Peso                | Peso asignado a este tipo de relación según importancia semántica.                          | Usado para calcular el score ponderado global.                                                                                      |
| **weighted_type_match_score**     | Métrica             | Suma ponderada de todos los matches por tipo de relación.                                   | **Mayor = el hotel recomendado coincide mejor con el historial del usuario**, considerando la importancia de cada tipo de relación. |

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




