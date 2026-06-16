# 🏨 Sistema de Recomendación XAI para Hoteles - TFM MUSII

**Trabajo de Fin de Máster** - Sistema de recomendación explicable basado en grafos de conocimiento e interacciones de usuarios con hoteles.

Este repositorio implementa los componentes actuales del pipeline XAI:
- 📦 Carga de datos en Neo4j
- 🧠 Extracción de subgrafos KG y CF
- 📊 Cálculo de métricas explicables
- 🧪 Evaluación de explicaciones con AggDiv, IXD, MIL y ECS

---

## 📌 Resumen del flujo actual

1. docker/loader/load_databases.py carga los CSV de entrada en dos bases de datos Neo4j:
   - interactions
   - knowledge
2. src/extraccion_algoritmos/pipeline.py consume las recomendaciones del modelo y genera métricas explicativas KG y CF.
3. src/evaluacion/pipeline.py toma los CSV resultantes y calcula métricas globales de evaluación XAI.
4. src/visualizacion/ contiene notebooks para explorar y visualizar resultados.

---

## 📁 Estructura actual del repositorio

`
Sistema_recomendacion_xai_TFM_MUSII_CMN/
├── COMANDOS.md
├── config_mode.py
├── README.md
├── run.sh
├── data/
│   ├── raw/
│   │   └── raw.txt
│   └── recomendaciones_del_modelo/
│       └── recomendaciones_del_modelo.txt
├── docker/
│   ├── docker-compose.yml
│   └── loader/
│       ├── Dockerfile
│       ├── load_databases.py
│       └── requirements.txt
├── logs/
├── output/
└── src/
    ├── evaluacion/
    │   ├── metricas_evaluacion.py
    │   └── pipeline.py
    ├── extraccion_algoritmos/
    │   ├── pipeline.py
    │   ├── extraccion_metricas_conocimiento/
    │   │   └── métricas.py
    │   └── extraccion_metricas_interaccion/
    │       └── métricas.py
    ├── extraccion_subgrafos/
    │   ├── subgrafo_conocimiento/
    │   │   ├── requirements.txt
    │   │   ├── utils_interactions.py
    │   │   └── utils_knowledge.py
    │   └── subgrafo_interaccion/
    │       └── utils_interaction_patterns.py
    └── visualizacion/
        ├── visualizacion_metricas.ipynb
        └── visualizacion_tablas_metricas.ipynb
`

> Nota: config_mode.py y 
un.sh contienen artefactos de una estructura anterior. Para la ejecución actual utiliza directamente los comandos Python descritos más abajo.

---

## ⚙️ Requisitos previos

Recomendado para Windows / Linux:
- Python 3.8+ instalado
- Docker y Docker Compose instalados
- pip actualizado

Instala las dependencias principales:

`ash
pip install pandas py2neo networkx
`

Si quieres usar el loader Docker, instala también las dependencias de docker/loader:

`ash
pip install -r docker/loader/requirements.txt
`

---

## 📥 Datos de entrada (qué se espera)

### 1) data/raw/grafo_interaccion_datos_train.csv
CSV de interacciones usuario-hotel que alimenta la base Neo4j interactions.
Columnas esperadas:
- user_id
- usiness_id
- 
ating

### 2) data/raw/grafo_conocimiento_datos_hoteles.csv
CSV de propiedades hoteleras que alimenta la base Neo4j knowledge.
Columnas esperadas (al menos algunas):
- item_id
- 
ame
- city
- state
- postal_code
- latitude
- longitude
- stars
- 
eview_count
- is_open
- category
- ttribute_key
- ttribute_value

### 3) data/recomendaciones_del_modelo/relacion_usuario_rating_recomendador*.csv
CSV de recomendaciones de modelos para explicar.
Columnas obligatorias:
- usuario
- 
egocio

Nombre de archivos usados por el pipeline:
- 
elacion_usuario_rating_recomendador.csv → algoritmo ase
- 
elacion_usuario_rating_recomendador_FunkSVD.csv → algoritmo FunkSVD
- 
elacion_usuario_rating_recomendador_<ALGORITMO>.csv → algoritmo <ALGORITMO>

> Si no existen estos CSV, el pipeline no procesará recomendaciones.

---

## 🧠 Qué hace cada componente

### docker/loader/load_databases.py
- Conecta a Neo4j usando py2neo.
- Crea las bases de datos interactions y knowledge si no existen.
- Borra los nodos existentes de cada base antes de recargar.
- Inserta relaciones (:User)-[:RATED]->(:Business) en interactions.
- Inserta (:Business)-[:RELATION]->(:Node) en knowledge para atributos como nombre, ciudad, categoría, coordenadas, etc.

### src/extraccion_subgrafos/subgrafo_conocimiento/utils_interactions.py
- Extrae el histórico de hoteles valorados por un usuario desde la base interactions.

### src/extraccion_subgrafos/subgrafo_conocimiento/utils_knowledge.py
- Recupera el subgrafo KG cercano a un conjunto de hoteles.
- Devuelve los nodos y relaciones relacionados con cada hotel de entrada.

### src/extraccion_subgrafos/subgrafo_interaccion/utils_interaction_patterns.py
- Añade un enlace temporal usuario-hotel recomendado sin 
ating.
- Extrae el patrón colaborativo:
  Usuario_Objetivo -> Hotel_Compartido <- Usuario_Intermedio -> Hotel_Recomendado
- Elimina el enlace temporal al terminar.
- Devuelve los nodos y relaciones del subgrafo CF.

### src/extraccion_algoritmos/pipeline.py
Es el pipeline principal actual. Su función es:
- Leer todos los CSV de recomendaciones desde data/recomendaciones_del_modelo/
- Para cada par (usuario, hotel_recomendado):
  - Extraer subgrafo KG con los hoteles históricos del usuario y el hotel recomendado
  - Calcular métricas KG
  - Extraer subgrafo CF y calcular métricas CF
- Guardar resultados por usuario y métrica
- Opcionalmente generar archivos de debug JSON y texto

### src/extraccion_algoritmos/extraccion_metricas_conocimiento/métricas.py
Métricas KG implementadas:
- kg_num_propiedades_compartidas
- kg_ratio_propiedades_compartidas
- kg_peso_ponderado_perfil
- kg_jaccard_similarity

Estas métricas miden cuánto comparte el hotel recomendado con los hoteles históricos del usuario en términos de atributos del grafo de conocimiento.

### src/extraccion_algoritmos/extraccion_metricas_interaccion/métricas.py
Métricas CF implementadas:
- cf_degree_hotel
- cf_ratio_usuarios_compartidos
- cf_norm_degree_hotel
- cf_betweenness_hotel

Estas métricas evalúan la fuerza explicativa de los hoteles compartidos en el subgrafo colaborativo.

### src/evaluacion/pipeline.py
Calcula métricas de evaluación XAI sobre los resultados de los CSV generados por el pipeline anterior.
- Detecta modelos / carpetas de salida en output/
- Procesa fuentes kg y cf
- Genera CSV de evaluación global

### src/evaluacion/metricas_evaluacion.py
Métricas de evaluación implementadas:
- AggDiv  → Diversidad agregada de explicadores por usuario
- IXD    → Diversidad inter-explicación entre recomendaciones
- MIL    → Mean Inter-List Diversity a nivel de sistema
- ECS    → Coherencia de explicaciones para hotel

---

## ▶️ Cómo ejecutar el pipeline completo

### 1) Levantar Neo4j y cargar datos

Desde la raíz del repositorio:

`ash
cd docker
docker-compose up --build
`

Esto arranca Neo4j y ejecuta el cargador docker/loader/load_databases.py.

### 2) Ejecutar el pipeline de métricas KG/CF

Desde la raíz del repositorio:

`ash
python src/extraccion_algoritmos/pipeline.py --modo muestra
`

Opciones útiles:
- --modo muestra → usa solo los usuarios definidos en --usuarios (por defecto [3, 35])
- --modo semi → toma las primeras 5 recomendaciones por usuario
- --modo completo → procesa todas las recomendaciones disponibles
- --usuarios 3 35 → lista de usuarios para modo muestra
- --debug → guarda JSONs y textos de validación en output/debug/
- --hotel 45 → en modo debug, filtra a un único hotel recomendado
- --csv-recomendaciones <archivo.csv> → procesar un CSV concreto

### 3) Ejecutar el pipeline de evaluación XAI

`ash
python src/evaluacion/pipeline.py --modo muestra --fuente kg cf
`

Opciones importantes:
- --modo muestra|semi|completo
- --fuente kg cf → analiza tanto métricas kg como cf
- --ks 1 3 5 → cutoffs para AggDiv, IXD, MIL y ECS
- --modelo <nombre> → nombres de modelos recomendadores concretos para evaluar
- --ecs-min-usuarios 2 → mínimo usuarios por hotel para ECS

> Nota: la evaluación requiere que los resultados del pipeline de métricas ya existan en output/.

---

## 📤 Salidas generadas

### Salidas de métricas KG/CF
- output/<algoritmo>/metricas_grafo_conocimiento_<modo>/...csv
- output/<algoritmo>/metricas_grafo_interaccion_<modo>/...csv

Ejemplos:
- kg_usuario_3_kg_num_propiedades_compartidas_20240615_123456.csv
- cf_usuario_35_cf_betweenness_hotel_20240615_123456.csv

### Salidas de debug
Si se ejecuta con --debug:
- output/debug/kg_user{U}_hotel{H}_subgrafo.json
- output/debug/cf_user{U}_hotel{H}_subgrafo.json
- output/debug/validacion_kg_user{U}_hotel{H}.txt
- output/debug/validacion_cf_user{U}_hotel{H}.txt

### Salidas de evaluación
- output/metricas_evaluacion_muestra/
- output/metricas_evaluacion_semi/
- output/metricas_evaluacion_completo/

Cada CSV de evaluación contiene métricas por usuario, por sistema o por hotel dependiendo de la estrategia.

### Logs
- logs/pipeline_<modo>_*.log
- logs/pipeline_evaluacion_<modo>_*.log

---

## 🧪 Ejemplo de ejecución

1. Cargar Neo4j:
   `ash
   cd docker
   docker-compose up --build
   `
2. Procesar recomendaciones en modo muestra:
   `ash
   cd ..
   python src/extraccion_algoritmos/pipeline.py --modo muestra --debug
   `
3. Evaluar resultados:
   `ash
   python src/evaluacion/pipeline.py --modo muestra --fuente kg cf
   `

---

## 💡 Recomendaciones y consideraciones

- Asegúrate de que los CSV de entrada existen en data/raw/ y data/recomendaciones_del_modelo/.
- El script docker/loader/load_databases.py asume columnas específicas en los CSV.
- 
un.sh en la raíz contiene rutas antiguas de otro entorno y no es fiable sin modificar.
- Usa --debug para depurar subgrafos y verificar la extracción KG/CF.
- config_mode.py es un helper legado y no forma parte obligatoria del pipeline actual.

---

## 📂 Nota sobre los datos actuales en este repositorio

En el árbol actual, data/raw/ sólo contiene 
aw.txt y data/recomendaciones_del_modelo/ sólo contiene 
ecomendaciones_del_modelo.txt.
Para ejecutar el pipeline correctamente, reemplaza esos ficheros con los CSV reales esperados:
- grafo_interaccion_datos_train.csv
- grafo_conocimiento_datos_hoteles.csv
- 
elacion_usuario_rating_recomendador*.csv

---

## 📌 Lógica de la solución

### KG (Grafo de Conocimiento)
1. Recupera hoteles históricos del usuario a partir de interactions.
2. Consulta Neo4j knowledge para obtener atributos del hotel recomendado y de los hoteles históricos.
3. Calcula métricas basadas en la intersección y similitud de propiedades.

### CF (Grafo de Interacción)
1. Agrega temporalmente una arista entre el usuario y el hotel recomendado.
2. Busca patrones colaborativos de tipo:
   Usuario_Objetivo -> Hotel_Compartido <- Usuario_Intermedio -> Hotel_Recomendado
3. Calcula métricas de centralidad y diversidad en el subgrafo resultante.
4. Elimina la arista temporal para dejar los datos originales intactos.

### Evaluación XAI
- AggDiv mide la diversidad agregada de explicadores por usuario.
- IXD mide la diversidad inter-explicación entre recomendaciones.
- MIL mide la diversidad entre listas de explicadores de usuarios distintos.
- ECS mide la consistencia de explicaciones para el mismo hotel recomendado.

---

## ✅ Resultado esperado

Al final del pipeline deberías obtener:
- métricas KG/CF estructuradas por usuario y top explicadores
- CSVs de evaluación global en output/
- logs y artefactos de debug para validar el razonamiento XAI

Si necesitas adaptar el repositorio a una versión más completa, el punto clave es mantener un flujo:
CSV entrada -> Neo4j -> extracción KG/CF -> cálculo métricas -> evaluación XAI.
