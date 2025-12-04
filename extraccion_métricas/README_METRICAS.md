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

### **2. Path Count / Path Multiplicity**

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

---

## Métricas Basadas en Centralidad (`metrics_centrality.py`)

Estas métricas analizan la **importancia estructural** de los atributos dentro del Knowledge Graph.
Evalúan si una explicación se basa en propiedades que realmente son relevantes o influyentes dentro del grafo.

### **1. Degree Centrality**

Número de hoteles conectados a un atributo.
Atributos populares → explicaciones más universales.

### **2. Normalized Degree Centrality**

El grado se normaliza entre 0 y 1.
Permite comparar atributos en grafos de distinto tamaño.

### **3. Betweenness Centrality**

Mide cuántas veces un atributo actúa como “puente” en caminos mínimos.
Útil para detectar atributos clave, aunque en grafos pequeños suele ser baja.

### **4. Closeness Centrality**

Evalúa qué tan cerca está un atributo del resto del grafo.
Atributos más cercanos → más relevantes para el sistema.

### **5. Eigenvector Centrality**

Mide si un atributo está conectado con otros atributos también importantes.
Indica influencia estructural.

### **6. PageRank**

Versión más estable de centralidad basada en enlaces.
Muy usada en sistemas explicables basados en grafos.

### **7. Harmonic Centrality**

Similar a closeness, pero más robusta cuando no hay conexiones directas.
Suma los inversos de las distancias.

### **8. Attribute Influence Score**

Combina la centralidad con su capacidad de diferenciación (AMF).
Mide cuánta influencia real tiene una propiedad al explicar recomendaciones.

---

# Métricas Basadas en Contenido/Atributos (`metrics_content.py`)

Estas métricas analizan directamente los **atributos** del hotel recomendado y cómo se relacionan con los atributos de los hoteles consumidos por el usuario.

### **9. Attribute Match Frequency (AMF)**

Indica qué proporción de los hoteles consumidos tiene un atributo presente en el recomendado.
Mide afinidad directa entre gustos del usuario y atributos del ítem.

### **10. Attribute Frequency (TF_user)**

Frecuencia absoluta de un atributo dentro de los hoteles consumidos.
Atributos frecuentes → representan bien el perfil del usuario.

### **11. Attribute TF-IDF (Discriminative Feature Score)**

Destaca atributos muy frecuentes para el usuario pero poco comunes en el catálogo.
Sirve para identificar preferencias “únicas”.

### **12. Attribute Contribution Score**

Cuantifica cuánto contribuye un atributo específico a justificar la recomendación.
Es la combinación entre frecuencia del atributo en los consumos y presencia en el recomendado.

### **13. Attribute Presence Ratio (APR)**

Proporción de atributos del recomendado que el usuario ya ha consumido antes.

### **14. Attribute Overlap Count**

Número total de atributos compartidos entre hotel recomendado y consumidos.

### **15. Attribute Novelty**

Detecta si un atributo es nuevo para el usuario.
1 = nuevo, 0 = ya conocido.

### **16. Attribute Specificity (Inverse Popularity)**

Da más importancia a atributos raros en el catálogo.
Atributos poco comunes → más informativos.

### **17. Attribute Stability**

Normaliza la frecuencia del atributo dentro del historial del usuario.
Atributos estables = preferencias firmes.

### **18. Attribute Variability**

Variabilidad (varianza/desviación estándar) de un atributo entre consumidos.
Baja variabilidad → atributo representativo del usuario.

---

# Métricas Basadas en Ejemplos (`metrics_examples.py`)

Estas métricas comparan el recomendado con los **hoteles consumidos** para generar explicaciones basadas en ejemplos.

### **19. Example Similarity Score**

Similitud entre el recomendado y un hotel consumido usando Jaccard o atributos.

### **20. Most Similar Consumed Example**

Selecciona el ejemplo (hotel consumido) más similar al recomendado.

### **21. Least Similar Consumed Example (Contrastive)**

El hotel consumido menos similar.
Útil para explicaciones tipo “por qué este y no aquel”.

### **22. Mean Example Similarity**

Similitud promedio del recomendado con todos los hoteles consumidos.

### **23. k-Nearest Example Strength**

Suma de similitudes de los k consumidos más parecidos.

### **24. Example Support Score (por atributo)**

Cuántos consumidos tienen un atributo del recomendado.

### **25. Relative Example Strength**

Support normalizado por el total de consumidos.

### **26. Example Density**

Frecuencia del atributo dentro del total de atributos consumidos.

### **27. Example Coverage**

Porcentaje de consumidos que comparten al menos un atributo con el recomendado.

### **28. Example Consensus Score**

Promedio del número de atributos compartidos → mide homogeneidad de la explicación.

### **29. Example Disagreement Score**

Variabilidad en la similitud entre consumidos y recomendado.

### **30. Prototype Example Score**

Selecciona el ejemplo más representativo del usuario (centroide).
Luego compara su similitud con el recomendado.

---

# Métricas de Similitud (`metrics_similarity.py`)

Evaluan la similitud entre consumidos y recomendado a nivel de atributos o vectores.

### **31. Jaccard Similarity**

Similitud de conjuntos basada en atributos compartidos.

### **32. Cosine Similarity**

Similitud vectorial entre representaciones de atributos.

### **33. Shared Attribute Count**

Número total de atributos compartidos.

### **34. Weighted Shared Attribute Score**

Versión ponderada usando pesos por atributo.

### **35. Shared Category Count**

Conteo específico de categorías compartidas.

### **36. Shared Location Count**

Coincidencias de ubicación (ciudad, país, región…).

### **37. Category Alignment Score**

Proporción de categorías del recomendado que coinciden con las del usuario.

### **38. Path Count (Graph)**

Cantidad de caminos en el KG entre consumido y recomendado.

### **39. Path Length (Graph)**

Distancia más corta o promedio en el KG.

### **40. Weighted Knowledge Path Score (KPS)**

Suma de pesos de todos los caminos relevantes.

---

# Métricas de Popularidad (`metrics_popularity.py`)

Evalúan lo comunes o raros que son los atributos.

### **41. Attribute Popularity**

Número de hoteles conectados al atributo.

### **42. Attribute Popularity Rank**

Percentil del atributo respecto al catálogo.

### **43. Inverse Popularity**

Atributos menos populares → más interesantes.

### **44. Commonality Score**

Cuántos usuarios han consumido ese atributo.
Requiere histórico de interacción.

---

# Métricas de Diversidad (`metrics_diversity.py`)

### **45. Explanation Type Diversity**

Número de tipos de relación usados en las explicaciones.

### **46. Attribute Diversity del recomendado**

Número de tipos de atributos presentes en el ítem recomendado.

### **47. Cross-Explanation Diversity**

Diversidad entre explicaciones generadas para un mismo usuario.

---

# Métricas de Recencia (`metrics_recency.py`)

### **48. Recency Score**

Da más peso a interacciones recientes.

### **49. Normalized Recency Rank**

Normaliza la recencia respecto al historial completo.

---

# Métricas de Novedad/Serendipia (`metrics_novelty.py`)

### **50. Novelty Count**

Número de atributos nuevos del recomendado.

### **51. Novelty Ratio**

Porcentaje de atributos nuevos del recomendado.

### **52. Surprise Score**

Novedad × rareza (inversa de popularidad).
Modelo típico de “sorpresa”.

---

# Métricas de Cobertura de Preferencias (`metrics_coverage.py`)

### **53. Preference Coverage**

Proporción de preferencias del usuario cubiertas por el recomendado.

### **54. Blind-Spot Coverage**

Información nueva aportada:
1 – Coverage.

---

# Métricas por Tipo de Relación (`metrics_type_relationship.py`)

### **55. Type-Specific Match Frequency**

Coincidencias específicas según tipo:

* CityMatch
* CategoryMatch
* AmenityMatch

### **56. Weighted Type Match Score**

Combina los tipos anteriores con pesos.


---

# 📘 Tabla Resumen de Métricas

| Métrica                          | Tipo        | Descripción breve                                                   | Archivo                        |
| -------------------------------- | ----------- | ------------------------------------------------------------------  | -----------------------------  |
| **Path Length**                  | Camino      | Saltos entre hotel consumido y recomendado.                         | `metrics_path.py`              |
| **Path Count**                   | Camino      | Número de caminos explicativos.                                     | `metrics_path.py`              |
| **Shared-Property Weight Score** | Camino      | Suma de pesos de propiedades compartidas.                           | `metrics_path.py`              |
| **Path Type Variety**            | Camino      | Número de tipos de relación compartidos.                            | `metrics_path.py`              |
| **Path Type Frequency**          | Camino      | Frecuencia de cada tipo de relación entre hoteles.                  | `metrics_path.py`              |
| **Path Confidence Score**        | Camino      | Suma de pesos de tipos de relación.                                 | `metrics_path.py`              |
| **Degree Centrality**            | Centralidad | Cantidad de conexiones del atributo.                                | `metrics_centrality.py`        |
| **Normalized Degree Centrality** | Centralidad | Grado normalizado entre 0 y 1.                                      | `metrics_centrality.py`        |
| **Betweenness Centrality**       | Centralidad | Atributo como puente en el grafo.                                   | `metrics_centrality.py`        |
| **Closeness Centrality**         | Centralidad | Proximidad del atributo al resto.                                   | `metrics_centrality.py`        |
| **Eigenvector Centrality**       | Centralidad | Importancia según conexiones con otros nodos importantes.           | `metrics_centrality.py`        |
| **PageRank**                     | Centralidad | Popularidad del atributo según enlaces.                             | `metrics_centrality.py`        |
| **Harmonic Centrality**          | Centralidad | Suma de 1/distancia con otros nodos.                                | `metrics_centrality.py`        |
| **Attribute Influence Score**    | Centralidad | Influencia combinada: centralidad × AMF.                            | `metrics_centrality.py`        |
| Métricas de Contenido            | Contenido   | Atributos compartidos, frecuencia, TF-IDF, estabilidad, novedad     | `metrics_content.py`           |
| Métricas basadas en Ejemplos     | Ejemplos    | Similitud con consumidores, ejemplos más/menos parecidos, consensus | `metrics_examples.py`          |
| Métricas de Similitud            | Similitud   | Jaccard, cosine, atributos compartidos, KPS, paths en KG            | `metrics_similarity.py`        |
| Popularidad                      | Popularidad | Qué tan común es un atributo                                        | `metrics_popularity.py`        |
| Diversidad                       | Diversidad  | Diversidad de explicaciones y atributos                             | `metrics_diversity.py`         |
| Recencia                         | Tiempo      | Peso a interacciones recientes                                      | `metrics_recency.py`           |
| Novedad/Serendipia               | Novedad     | Atributos nuevos, inesperados, sorpresa                             | `metrics_novelty.py`           |
| Cobertura                        | Cobertura   | Qué parte del perfil cubre el recomendado                           | `metrics_coverage.py`          |
| Tipo de Relación                 | Relaciones  | Coincidencias por tipo y versión ponderada                          | `metrics_type_relationship.py` |

