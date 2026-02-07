# Descripción
-----------
Esta carpeta contiene el código y los resultados relacionados con el bloque de cálculo de métricas (bloque_score_abstracto) y la generación de explicaciones basadas en ejemplos. Los pasos principales son: calcular métricas para cada usuario y, opcionalmente, generar explicaciones a partir de esos resultados.

# Estructura
---------
- `bloque_score_abstracto/`
  - `calcular.py` : Script principal que carga las recomendaciones y aplica las métricas definidas en `métricas.py` para cada usuario. Produce archivos CSV con las métricas por usuario.
  - `métricas.py` : Implementación de las estrategias/funciones de métricas usadas por `calcular.py`.
- `explicaciones_basadas_ejemplos/`
  - `crear_explicaciones.py` : Script que usa datos y/o resultados de métricas para crear explicaciones basadas en ejemplos (puede leer archivos en `resultados_scores/` o en `explicaciones_basadas_ejemplos/data/`).
- `resultados_scores/` : Carpeta de salida que contiene los CSV generados por `calcular.py` (por ejemplo `metricas_completas_usuario_3.csv`).

# Orden de ejecución (recomendado)
-------------------------------
1. Preparar los datos de entrada
   - Asegúrate de que el archivo `relacion_usuario_rating_recomendador.csv` esté disponible en `data_recommender/` a partir del directorio de trabajo.

2. Generar explicaciones (opcional)
   - Una vez que `resultados_scores/` contiene los CSV, puedes ejecutar `explicaciones_basadas_ejemplos/crear_explicaciones.py` para generar los ficheros de explicaciones.

     ```bash
     python 3_explicaciones_basadas_ejemplos/explicaciones_basadas_ejemplos/crear_explicaciones.py
     ```

3. Calcular métricas
   - Ejecutar desde la propia carpeta `bloque_score_abstracto`:

     ```bash
     cd 3_explicaciones_basadas_ejemplos/bloque_score_abstracto
     python calcular.py
     ```

    - Nota sobre rutas: `calcular.py` usa rutas relativas para localizar `data_recommender` y `resultados_scores`. La ruta que se resuelva dependerá del directorio de trabajo desde el que ejecutes el script:
     - Si ejecutas desde `bloque_score_abstracto/`, el script buscará `data_recommender` relativo a esa carpeta; en ese caso, mueve o crea `data_recommender/` dentro de `3_explicaciones_basadas_ejemplos/` o modifica las rutas en el script.



