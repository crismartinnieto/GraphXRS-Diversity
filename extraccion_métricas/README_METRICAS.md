# 📘 **README — Metric Toolkit for Explainable Recommender Systems (XAI-RS)**

Este repositorio contiene una colección sistemática y depurada de **55 métricas únicas** para explicar recomendaciones de items (hoteles) en sistemas basados en contenido, grafos y ejemplos de usuario.
Incluye métricas para:
✔️ similitud,
✔️ grafos (KGRS),
✔️ atributos,
✔️ explicaciones basadas en ejemplos,
✔️ diversidad,
✔️ popularidad,
✔️ serendipia,
✔️ prototipos,
✔️ cobertura del perfil del usuario.

El objetivo es proporcionar una **guía práctica** y formalizada para investigadores y desarrolladores de **Explainable AI for Recommender Systems (XAI-RS)**.

---

# ---------------------------------------------------------

# 🔵 **1. Path-Based Metrics (Knowledge Graph)**

## 1. **Path Count**

Número total de rutas entre un item consumido y el recomendado.

[
PathCount(h, rec) = |\text{Paths}(h, rec)|
]

---

## 2. **Path Length**

Longitud promedio o mínima de las rutas.

[
PathLength = \frac{1}{|Paths|}\sum_{p \in Paths} |p|
]

---

## 3. **Path Type Variety**

Cantidad de tipos distintos de relaciones usadas en rutas.

---

## 4. **Path Type Frequency**

Frecuencia de cada tipo de relación.

---

## 5. **Path Confidence Score**

Suma de los pesos de las rutas:

[
PCS = \sum_{p \in Paths} weight(p)
]

---

# ---------------------------------------------------------

# 🔵 **2. Centrality-Based Metrics**

Miden la importancia estructural del item en el grafo.

6. Degree Centrality
7. Normalized Degree Centrality
8. Betweenness Centrality
9. Closeness Centrality
10. Eigenvector Centrality
11. PageRank Centrality
12. Harmonic Centrality
13. Influence Score

Todas estas métricas son las clásicas del análisis de grafos (Network Science).

---

# ---------------------------------------------------------

# 🔵 **3. Attribute / Property Metrics**

## 14. **Attribute Overlap Count**

Número de atributos compartidos.

[
Overlap(h,rec) = |Props(h) \cap Props(rec)|
]

---

## 15. **Attribute Overlap Ratio — Jaccard Similarity**

[
Jaccard(h,rec)=\frac{|Props(h)\cap Props(rec)|}{|Props(h)\cup Props(rec)|}
]

---

## 16. **Cosine Similarity (vector binario de atributos)**

[
Cos(h)=\frac{v_h \cdot v_{rec}}{|v_h||v_{rec}|}
]

---

## 17. TF (Term Frequency of Attributes)

## 18. TF-IDF Attribute Score

## 19. Attribute Contribution Score

(Cuánto aporta cada atributo a la similitud total.)

## 20. Attribute Novelty Score

Atributos nuevos respecto al historial del usuario.

## 21. Attribute Specificity Score

Qué tan raros o únicos son los atributos.

## 22. Attribute Stability Score

Persistencia del atributo en el perfil del usuario.

## 23. Attribute Variability Score

Variación del atributo en el conjunto consumido.

---

# ---------------------------------------------------------

# 🔵 **4. Category & Location Metrics**

## 24. Category Alignment Score (CAS)

[
CAS = \frac{|Cat(rec) \cap Cat(H_{user})|}{|Cat(rec)|}
]

---

## 25. Shared Category Count

Número de categorías en común.

## 26. Shared Location Count

Coincidencias en ciudad/estado/país/ZIP/coordenadas.

---

# ---------------------------------------------------------

# 🔵 **5. Weighted Attribute Metrics**

## 27. Weighted Shared Attribute Score

[
Score(h)=\sum_{p\in Props(h)\cap Props(rec)} w(p)
]

Ejemplo de pesos: categorías=3, ubicación=2, amenidades=1.

---

# ---------------------------------------------------------

# 🔵 **6. Case-Based / Example-Based Metrics**

Basado en ejemplos reales consumidos por el usuario.

## 28. Most Similar Consumed Example

[
Best(h)=\max_h Similarity(h,rec)
]

## 29. Least Similar Example

[
Worst(h)=\min_h Similarity(h,rec)
]

## 30. Example Similarity Score

(Similaridad general, usando cualquier métrica.)

## 31. Mean Example Similarity

[
Mean = \frac{1}{k}\sum_i Similarity(h_i,rec)
]

## 32. Example Support Score

[
Support(p)=|{h: p\in Props(h)}|
]

## 33. Example Strength

[
Strength = \frac{Support(p)}{|H_{user}|}
]

## 34. Example Density

Soporte normalizado por número total de atributos.

## 35. Example Coverage

[
Coverage = \frac{#h \text{ con algún atributo compartido}}{#h}
]

## 36. Example Consensus Score

Promedio de atributos compartidos.

## 37. Example Disagreement Score

[
Var(Similarity(h_i,rec))
]

## 38. k-Nearest Example Strength (k-NES)

[
kNES = \sum_{h\in top-k} Similarity(h,rec)
]

## 39. Prototype Example Similarity

Item más representativo del perfil:

[
Prototype = \arg\min_h Dist(h, \text{centroide})
]

---

# ---------------------------------------------------------

# 🔵 **7. Popularity Metrics**

40. Popularity Score
41. Popularity Rank
42. Inverse Popularity Score
43. Commonality Score

---

# ---------------------------------------------------------

# 🔵 **8. Diversity Metrics**

44. Explanation Type Diversity
45. Attribute Diversity Score
46. Cross-explanation Diversity

---

# ---------------------------------------------------------

# 🔵 **9. Recency Metrics**

47. Recency Score
48. Normalized Recency Rank

---

# ---------------------------------------------------------

# 🔵 **10. Novelty & Serendipity**

49. Novelty Count
50. Novelty Ratio
51. Surprise Score

---

# ---------------------------------------------------------

# 🔵 **11. Coverage Metrics**

52. Preference Coverage
53. Blind-Spot Coverage

---

# ---------------------------------------------------------

# 🔵 **12. Type-Specific Metrics**

54. Type-Specific Match Frequency
55. Weighted Type Match Score

