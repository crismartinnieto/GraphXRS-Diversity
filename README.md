# 🏨 Sistema de Recomendación XAI para Hoteles - TFM MUSII

**Trabajo de Fin de Máster** - Sistema de recomendación explicable basado en grafos de conocimiento e interacciones de usuarios con hoteles.

Este proyecto implementa una arquitectura completa para:
- 📊 Cargar y gestionar grafos de conocimiento en **Neo4j**
- 👥 Procesar interacciones usuario-hotel
- 🔍 Extraer subgrafos personalizados para explicabilidad
- 📈 Calcular métricas de recomendación
- 📊 Visualizar resultados y explicaciones

---

## 📚 Descripción General

El sistema utiliza un enfoque basado en **grafos de conocimiento (KG)** y **explicabilidad (XAI)** para proporcionar recomendaciones de hoteles con justificaciones claras basadas en propiedades, ubicación, categorías y similitudes con preferencias históricas del usuario.

### 🎯 Objetivo del Proyecto

Este TFM implementa un **sistema de recomendación de hoteles basado en grafos de conocimiento con capacidades XAI (Explainable AI)**. La principal innovación es la capacidad de:

1. **Proporcionar recomendaciones precisas** utilizando grafos de conocimiento sobre hoteles
2. **Explicar por qué se recomienda cada hotel** mediante subgrafos que muestran conexiones relevantes
3. **Analizar la calidad de las recomendaciones** con múltiples métricas de explicabilidad
4. **Visualizar el razonamiento** detrás de cada recomendación

### 🏗️ Arquitectura Técnica

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                      │
│              (Visualizador de Métricas - Futuro)            │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE ANÁLISIS                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Extracción de Métricas de Explicabilidad            │   │
│  │ • Centralidad • Diversidad • Novedad                 │   │
│  │ • Similitud • Rutas • Popularidad • Cobertura        │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↑                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Cálculo de Scores y Cobertura                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                 CAPA DE PROCESAMIENTO                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Extracción de Subgrafos Personalizados              │   │
│  │ • Subgrafos usuario-hotel                            │   │
│  │ • Subgrafos completos por usuario                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          NEO4J (Grafos de Conocimiento)             │   │
│  │ ┌────────────────┐        ┌──────────────────────┐  │   │
│  │ │ interactions   │        │ knowledge            │  │   │
│  │ │ Usuario-Hotel  │        │ Hotel Properties     │  │   │
│  │ │ + Ratings      │        │ (Ubicación, etc)     │  │   │
│  │ └────────────────┘        └──────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                              ↑                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             Archivos CSV de Entrada                 │   │
│  │ • Interacciones train • Datos de hoteles            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 📦 Bases de Datos Neo4j

#### **Base `interactions`**
Almacena las relaciones de usuarios con hoteles:
```cypher
(:User {id: 3})-[:RATED {rating: 4.5}]->(:Business {id: 2963})
(:User {id: 3})-[:RATED {rating: 3.8}]->(:Business {id: 104})
```

#### **Base `knowledge`**
Grafo de conocimiento enriquecido sobre propiedades de hoteles:
```cypher
(:Business {id: 2963})
  -[:has_name]->(:Node {name: "Hotel Luxury"})
  -[:located_in_city]->(:Node {name: "Madrid"})
  -[:in_state]->(:Node {name: "Madrid"})
  -[:has_coordinates]->(:Node {name: "(40.4168, -3.7038)"})
  -[:has_rating]->(:Node {name: "4.5 stars"})
  -[:has_category]->(:Node {name: "Hotels"})
  -[:has_category]->(:Node {name: "Budget"})
  -[:has_attribute]->(:Node {name: "Amenities=WiFi"})
```

---

## 🗂️ Estructura del Proyecto

```
Sistema_recomendacion_xai_TFM_MUSII_CMN/
│
├── 📁 arquitectura_completa/         ⭐ PASO 1: Inicializar bases de datos
│   ├── docker-compose.yml
│   ├── loader/
│   │   ├── Dockerfile
│   │   ├── load_databases.py
│   │   ├── requirements.txt
│   │   └── data/
│   │       ├── grafo_interaccion_datos_train.csv
│   │       └── grafo_conocimiento_datos_hoteles.csv
│   └── volumes/
│       └── neo4j_data/               (Volumen persistente)
│
├── 📁 extraccion_subgrafo/           ⭐ PASO 2: Extraer subgrafos personalizados
│   ├── main_user_subgraph.py
│   ├── main_user_full_subgraph.py
│   ├── utils_interactions.py
│   ├── utils_knowledge.py
│   ├── save_graph.py
│   ├── requirements.txt
│   └── data/
│       ├── subgrafos/               (usuario-hotel individuales)
│       └── subgrafos_completos/     (por usuario)
│
├── 📁 extraccion_scores/             🔮 PASO 3: Calcular puntuaciones (Futuro)
│   ├── main.py
│   ├── requirements.txt
│   ├── src/
│   └── data/
│
├── 📁 extraccion_métricas/           📊 PASO 4: Análisis de métricas (Futuro)
│   ├── runner.py
│   ├── metrics_*.py
│   ├── csv_explicabilidad/
│   └── notebooks/
│
├── 📁 extraccion_prop/               🔧 PASO 5: Extracción de propiedades (Futuro)
│
├── 📁 visualizador_metricas/         📈 PASO 6: Visualización (Futuro)
│
├── 📁 data/                          📂 Datos de entrada
│
└── README.md                         (Este archivo)
```

---

## 🔄 Flujo de Ejecución del Proyecto

### **PASO 1: Inicializar bases de datos Neo4j** (`arquitectura_completa/`)
Crea e inicializa las dos bases de datos de Neo4j y carga los datos de entrada.

**Entrada:** CSVs con datos de usuarios, hoteles e interacciones  
**Salida:** Dos grafos en Neo4j (`interactions` y `knowledge`)

```bash
cd arquitectura_completa
docker-compose up
```

---

### **PASO 2: Extraer subgrafos** (`extraccion_subgrafo/`)
Consulta las bases de datos cargadas y genera subgrafos personalizados por usuario-hotel.

**Entrada:** Bases de datos Neo4j inicializadas + CSV de recomendaciones  
**Salida:** Archivos JSON con subgrafos para análisis

```bash
cd extraccion_subgrafo
python main_user_subgraph.py
python main_user_full_subgraph.py
```

---

### **PASO 3: Calcular Scores** (`extraccion_scores/`) - 🔮 En desarrollo
Calcula puntuaciones y métricas básicas de cobertura.

**Entrada:** Subgrafos JSON  
**Salida:** CSVs con scores

```bash
cd extraccion_scores
python main.py
```

---

### **PASO 4: Extraer Métricas** (`extraccion_métricas/`) - 📊 En desarrollo
Análisis profundo con métricas de centralidad, diversidad, similitud, novedad, etc.

**Entrada:** Subgrafos + Scores  
**Salida:** CSVs de métricas explicabilidad

```bash
cd extraccion_métricas
python runner.py
```

---

### **PASO 5: Extracción de Propiedades** (`extraccion_prop/`) - 🔧 En desarrollo
Procesa propiedades específicas de hoteles.

---

### **PASO 6: Visualización** (`visualizador_metricas/`) - 📈 En desarrollo
Genera visualizaciones interactivas de resultados.



---

## � Guía de Instalación Completa

### Requisitos Previos
Verificar que está instalado:

```bash
# Verificar Docker
docker --version
# Output esperado: Docker version 24.0.0 o superior

# Verificar Docker Compose
docker-compose --version
# Output esperado: Docker Compose version 2.0.0 o superior

# Verificar Python
python --version
# Output esperado: Python 3.8 o superior
```

### Paso 0: Clonar y Preparar el Repositorio

```bash
# Clonar el repositorio
git clone <TU_REPOSITORIO>
cd Sistema_recomendacion_xai_TFM_MUSII_CMN

# Ver estructura del proyecto
dir  # Windows
ls   # macOS/Linux

# Opcional: Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Paso 1: Inicializar Neo4j y Cargar Datos

Este paso es **OBLIGATORIO** y debe ejecutarse primero. Prepara la base de datos.

```bash
# Navegar al directorio del loader
cd arquitectura_completa

# Iniciar Docker Compose
docker-compose up --build

# Esperar los siguientes logs:
# ✅ Base 'interactions' creada/verificada
# ✅ Base 'knowledge' creada/verificada
# ✅ 'interactions': XXXX relaciones insertadas
# ✅ 'knowledge': XXXX relaciones insertadas
# ✅ Ambas bases de datos cargadas correctamente

# Una vez completado (sin Ctrl+C), abrir otra terminal
```

**Verificación:**
- Acceder a Neo4j Browser: http://localhost:7474
- Usuario: `neo4j`, Contraseña: `test12345`
- Ejecutar en Neo4j Browser:
```cypher
:use interactions
MATCH (n) RETURN count(n) as total_nodes;

:use knowledge
MATCH (n) RETURN count(n) as total_nodes;
```

### Paso 2: Extraer Subgrafos Personalizados

Una vez que Neo4j está inicializado, extraer los subgrafos.

```bash
# Navegar al directorio de extracción
cd ../extraccion_subgrafo

# Instalar dependencias
pip install -r requirements.txt

# Opción A: Extraer un usuario y hotel específico
python -c "
from main_user_subgraph import extract_user_subgraph
extract_user_subgraph(user_id=3, recommended_hotel=2963)
"

# Opción B: Extraer todos los usuarios y hoteles del CSV
python main_user_subgraph.py

# Opción C: Extraer subgrafos completos por usuario
python main_user_full_subgraph.py

# Verificar resultados
# Los archivos JSON se guardarán en:
# - data/subgrafos/user_X_hotel_Y.json
# - data/subgrafos_completos/user_X_full_subgraph.json
```

### Paso 3: Calcular Scores (Futuro)

```bash
cd ../extraccion_scores
pip install -r requirements.txt
python main.py
# Genera CSVs con scores en data/
```

### Paso 4: Extraer Métricas de Explicabilidad (Futuro)

```bash
cd ../extraccion_métricas
python runner.py
# Genera análisis de centralidad, diversidad, novedad, etc.
# Resultados en csv_explicabilidad/
```

### Paso 5-6: Propiedades y Visualización (Futuro)

```bash
cd ../extraccion_prop
python main.py

cd ../visualizador_metricas
# Ejecutar notebooks o scripts de visualización
```

---

## 📊 Descripción Detallada de cada Módulo

### 1. **Loader - Carga de Bases de Datos** (`arquitectura_completa/`)

#### 🎯 Propósito
Crear e inicializar dos bases de datos Neo4j completamente pobladas con:
- Relaciones usuario-hotel con ratings
- Grafo de conocimiento con propiedades de hoteles

#### 📥 Entrada
```
data/
├── grafo_interaccion_datos_train.csv
│   └── Columnas: user_id, business_id, rating
│   └── Ejemplo: 3, 2963, 4.5
│
└── grafo_conocimiento_datos_hoteles.csv
    └── Columnas: item_id, name, city, state, latitude, longitude, 
                  stars, review_count, category, is_open, attribute_key, 
                  attribute_value
    └── Ejemplo: 2963, "Hotel Luxury", "Madrid", "Madrid", 40.4168, 
                 -3.7038, 4.5, 250, "Hotels,Budget", 1, "Wifi", "Yes"
```

#### ⚙️ Procesos Ejecutados

**1. Crear bases de datos:**
```cypher
CREATE DATABASE interactions IF NOT EXISTS
CREATE DATABASE knowledge IF NOT EXISTS
```

**2. Cargar base `interactions`:**
- Crea nodos User y Business
- Establece relación RATED con rating
- Ejemplo:
```cypher
(:User {id: 3})-[:RATED {rating: 4.5}]->(:Business {id: 2963})
```

**3. Cargar base `knowledge`:**
- Crea Business para cada hotel
- Crea Node para cada propiedad
- Conecta con relaciones tipadas
- Ejemplo:
```cypher
(:Business {id: 2963})
  -[:has_name]->(:Node {name: "Hotel Luxury"})
  -[:located_in_city]->(:Node {name: "Madrid"})
  -[:has_rating]->(:Node {name: "4.5 stars"})
  -[:has_category]->(:Node {name: "Hotels"})
```

#### 📤 Salida
- Base `interactions` poblada con ~X usuarios y ~Y hoteles
- Base `knowledge` poblada con ~Z nodos y relaciones
- Logs detallados con progreso

#### 🚀 Ejecución
```bash
cd arquitectura_completa
docker-compose up --build
# Esperar a que termine (no interrumpir)
```

#### 📋 Archivos Clave
- `load_databases.py`: Script principal
- `docker-compose.yml`: Configuración de servicios
- `Dockerfile`: Imagen del contenedor
- `requirements.txt`: Dependencias Python

**Documentación completa:** Ver [arquitectura_completa/README.md](arquitectura_completa/README.md)

---

### 2. **Extracción de Subgrafos** (`extraccion_subgrafo/`)

#### 🎯 Propósito
Extraer subgrafos personalizados que muestren:
- Hoteles recomendados
- Historial de interacciones del usuario
- Conexiones en el grafo de conocimiento
- Justificaciones para recomendaciones

#### 📥 Entrada
```
Neo4j (bases interactions + knowledge)
+ 
data_recommender/relacion_usuario_rating_recomendador.csv
├── Columnas: user_id, recommended_hotel, rating, ...
└── Ejemplo: 3, 2963, 4.7, ...
```

#### ⚙️ Procesos

**Flujo para usuario 3, hotel recomendado 2963:**

1. **Obtener historial de usuario:**
```cypher
MATCH (u:User {id: 3})-[r:RATED]->(b:Business)
RETURN b.id as hotel_id, r.rating as rating
```
Resultado: [104, 1054, 1093, ...]

2. **Combinar hoteles:**
Hoteles a incluir = [2963] + [104, 1054, 1093, ...] = [hoteles del usuario + recomendación]

3. **Extraer subgrafo:**
```cypher
MATCH (h:Business {id: hotel_id})-[r]-(n)
RETURN h, r, n
```
Para cada hotel en la lista combinada

4. **Guardar en JSON:**
```json
{
  "nodes": [
    {"id": "2963", "label": "Business", "properties": {"id": "2963"}},
    {"id": "hotel_luxury", "label": "Node", "properties": {"name": "Hotel Luxury"}},
    {"id": "madrid", "label": "Node", "properties": {"name": "Madrid"}}
  ],
  "relationships": [
    {"source": "2963", "target": "hotel_luxury", "type": "has_name"},
    {"source": "2963", "target": "madrid", "type": "located_in_city"}
  ]
}
```

#### 📤 Salida

**Dos tipos de subgrafos:**

1. **Individuales usuario-hotel:**
   ```
   data/subgrafos/user_3_hotel_2963.json
   data/subgrafos/user_3_hotel_104.json
   data/subgrafos/user_3_hotel_1054.json
   ... (uno por cada recomendación)
   ```

2. **Completos por usuario:**
   ```
   data/subgrafos_completos/user_3_full_subgraph.json
   data/subgrafos_completos/user_35_full_subgraph.json
   ... (todos los hoteles del usuario en un grafo)
   ```

#### 🚀 Ejecución

```bash
cd extraccion_subgrafo

# Opción 1: Usuario y hotel específico
python -c "
from main_user_subgraph import extract_user_subgraph
extract_user_subgraph(user_id=3, recommended_hotel=2963)
"

# Opción 2: Procesar CSV completo (todos los usuarios)
python main_user_subgraph.py

# Opción 3: Subgrafos completos
python main_user_full_subgraph.py

# Opción 4: Ambos
python main_user_subgraph.py && python main_user_full_subgraph.py
```

#### 📋 Componentes

- **`main_user_subgraph.py`**: Script principal para individuales
- **`main_user_full_subgraph.py`**: Script para subgrafos completos
- **`utils_interactions.py`**: Consulta base `interactions`
- **`utils_knowledge.py`**: Extrae del grafo de conocimiento
- **`save_graph.py`**: Persiste en JSON

**Documentación completa:** Ver [extraccion_subgrafo/README.md](extraccion_subgrafo/README.md)

---

### 3. **Extracción de Scores** (`extraccion_scores/`) - 🔮 En desarrollo

#### 🎯 Propósito
Calcular métricas básicas de cobertura y scores preliminares para las recomendaciones.

#### 📥 Entrada
- Subgrafos JSON generados en PASO 2
- CSV de recomendaciones

#### 📤 Salida
```
data/
├── resultados_metricas_cobertura.csv
├── scores_recomendaciones.csv
└── cobertura_por_usuario.csv
```

#### 🚀 Ejecución
```bash
cd extraccion_scores
pip install -r requirements.txt
python main.py
```

---

### 4. **Extracción de Métricas de Explicabilidad** (`extraccion_métricas/`) - 📊 En desarrollo

#### 🎯 Propósito
Análisis profundo de las recomendaciones con múltiples métricas XAI.

#### 📊 Métricas Disponibles

| Métrica | Descripción | Archivo |
|---------|-------------|---------|
| **Centralidad** | Nodos importantes en el subgrafo (Degree, Betweenness, Closeness) | `metrics_centrality.py` |
| **Cobertura** | Qué tan bien explica el subgrafo | `metrics_coverage.py` |
| **Diversidad** | Variedad de tipos de propiedades | `metrics_diversity.py` |
| **Novedad** | Qué tan nuevo es el hotel recomendado | `metrics_novelty.py` |
| **Similitud** | Parecido con hoteles previos del usuario | `metrics_similarity.py` |
| **Rutas** | Caminos que conectan usuario con hotel | `metrics_path.py` |
| **Popularidad** | Rating y reviews del hotel | `metrics_popularity.py` |
| **Ejemplos** | Propiedades ejemplares | `metrics_examples.py` |

#### 📤 Salida
```
csv_explicabilidad/
├── metricas_usuario_3/
│   ├── hotel_2963_centrality.csv
│   ├── hotel_2963_coverage.csv
│   ├── hotel_2963_diversity.csv
│   └── ...
└── metricas_usuario_3_v1/
    └── ... (versión 1 de métricas)
```

#### 🚀 Ejecución
```bash
cd extraccion_métricas
python runner.py          # Ejecutar todas las métricas
python runner_compressed.py  # Versión comprimida
```

---

### 5. **Extracción de Propiedades** (`extraccion_prop/`) - 🔧 En desarrollo

#### 🎯 Propósito
Procesar y enriquecer propiedades específicas de hoteles.

#### 📋 Archivos
- `main.py`: Script principal
- `main_2.py`: Variante 2
- `visual.ipynb`: Visualización de propiedades

---

### 6. **Visualizador de Métricas** (`visualizador_metricas/`) - 📈 En desarrollo

#### 🎯 Propósito
Crear dashboards y visualizaciones interactivas de resultados.

#### 📋 Notebook
- `visualizacion_metricas_explicabilidad.ipynb`: Análisis visual

---

## 🔧 Troubleshooting y Solución de Problemas

### ❌ Problema: Docker no inicia

**Síntomas:**
```
Error response from daemon: ...
Failed to initialize docker
```

**Soluciones:**
```bash
# 1. Verificar que Docker está corriendo
docker ps

# 2. Si no está corriendo, iniciar Docker Desktop
# (En Windows/macOS, abrir la aplicación Docker Desktop)

# 3. Limpiar contenedores antiguos
docker-compose down
docker system prune -a

# 4. Reintentar
docker-compose up --build
```

### ❌ Problema: Neo4j no inicia después de Docker up

**Síntomas:**
```
Connection refused
Neo4j no responde en localhost:7687
```

**Soluciones:**
```bash
# 1. Esperar más tiempo (Neo4j tarda ~30 segundos en iniciar)
# El script espera 20s antes de conectar

# 2. Ver logs de Neo4j
docker logs <container_id_neo4j>

# 3. Verificar que el puerto 7687 no está en uso
netstat -an | findstr :7687  # Windows
lsof -i :7687               # macOS/Linux

# 4. Liberar el puerto y reiniciar
docker-compose down -v  # Eliminar volúmenes
docker-compose up --build
```

### ❌ Problema: Conexión rechazada a Neo4j desde Python

**Síntomas:**
```
py2neo.errors.ServiceUnavailable: Failed to establish connection
```

**Soluciones:**

```python
# 1. Verificar credenciales en utils_knowledge.py
from utils_knowledge import get_knowledge_graph

# 2. Probar conexión
try:
    graph = get_knowledge_graph()
    print("Conectado correctamente")
except Exception as e:
    print(f"Error de conexión: {e}")

# 3. Si ejecutas en el mismo ordenador:
uri = "bolt://localhost:7687"  # Cambiar 'neo4j' a 'localhost'

# 4. Si ejecutas en Docker:
uri = "bolt://neo4j:7687"      # Usar nombre del servicio
```

### ❌ Problema: No se encuentran datos en Neo4j

**Síntomas:**
```
0 nodos encontrados
Subgrafos vacíos
```

**Soluciones:**
```bash
# 1. Verificar que el loader completó
# Buscar en los logs: "✅ Ambas bases de datos cargadas correctamente"

# 2. Verificar en Neo4j Browser (http://localhost:7474)
:use interactions
MATCH (n) RETURN count(n);  # Debe retornar > 0

:use knowledge
MATCH (n) RETURN count(n);  # Debe retornar > 0

# 3. Si están vacíos, reiniciar loader
docker-compose restart neo4j
docker-compose up
```

### ❌ Problema: Python no encuentra módulos

**Síntomas:**
```
ModuleNotFoundError: No module named 'py2neo'
```

**Soluciones:**
```bash
# 1. Verificar que está en el entorno correcto
python -m pip list | grep py2neo

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Verificar Python version
python --version  # Debe ser >= 3.8

# 4. Reinstalar si es necesario
pip install --upgrade py2neo pandas networkx
```

### ❌ Problema: Archivos CSV no encontrados

**Síntomas:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/...'
```

**Soluciones:**
```bash
# 1. Verificar ruta
ls arquitectura_completa/loader/data/  # Debe estar aquí

# 2. Verificar nombres exactos
# Deben ser:
# - grafo_interaccion_datos_train.csv
# - grafo_conocimiento_datos_hoteles.csv

# 3. Verificar permisos de lectura
# Los archivos deben ser legibles
```

### ❌ Problema: Memoria insuficiente

**Síntomas:**
```
java.lang.OutOfMemoryError
Docker container killed
```

**Soluciones:**
```bash
# 1. Aumentar memoria de Docker
# En Docker Desktop Settings:
# Settings > Resources > Memory > Aumentar a 4-8 GB

# 2. Reducir dataset si es demasiado grande
# Usar un CSV más pequeño para testing

# 3. Usar docker-compose con límites
# Modificar docker-compose.yml:
services:
  neo4j:
    mem_limit: 4g
    memswap_limit: 4g
```

---

## 📈 Monitoreo y Logging

### Ver logs en tiempo real

```bash
# Logs del loader
docker logs -f <container_id> --tail 100

# Logs de Python local
python main_user_subgraph.py 2>&1 | tee execution.log

# Logs con timestamp
python -u main_user_subgraph.py > $(date +%Y%m%d_%H%M%S).log 2>&1
```

### Niveles de logging

El proyecto usa diferentes niveles:
```python
import logging
logging.basicConfig(level=logging.INFO)  # O DEBUG para más detalle
```

---

## 💾 Backup y Recuperación

### Hacer backup de Neo4j

```bash
# Exportar base de datos
docker exec neo4j neo4j-admin dump --database=interactions --to=/backup/interactions.dump
docker exec neo4j neo4j-admin dump --database=knowledge --to=/backup/knowledge.dump

# Copiar del contenedor
docker cp neo4j:/backup/ ./backup_local/
```

### Restaurar desde backup

```bash
# Copiar al contenedor
docker cp ./backup_local/interactions.dump neo4j:/backup/

# Restaurar
docker exec neo4j neo4j-admin load --from=/backup/interactions.dump --database=interactions --overwrite-destination
```

---

## 🧪 Testing y Validación

### Test de Conectividad

```bash
# Test conexión Neo4j
cd extraccion_subgrafo
python -c "
from utils_knowledge import get_knowledge_graph
graph = get_knowledge_graph()
print('Conexión exitosa')
result = graph.run('MATCH (n) RETURN count(n) as total').data()
print(f'Total de nodos: {result[0][\"total\"]}')
"

# Test de extracción
python -c "
from main_user_subgraph import extract_user_subgraph
result = extract_user_subgraph(user_id=3, recommended_hotel=2963)
print(f'Subgrafo guardado en: {result}')
"
```

### Validación de Datos

```bash
# Verificar estructura de JSON
python -c "
import json
with open('data/subgrafos/user_3_hotel_2963.json') as f:
    sg = json.load(f)
    print(f'Nodos: {len(sg[\"nodes\"])}')
    print(f'Relaciones: {len(sg[\"relationships\"])}')
"
```

---

## 📚 Referencias Técnicas

### Neo4j
- **Documentación oficial**: https://neo4j.com/docs/
- **Cypher Reference**: https://neo4j.com/docs/cypher-manual/current/
- **Browser**: http://localhost:7474

### Python Libraries
- **py2neo**: https://py2neo.org/
- **NetworkX**: https://networkx.org/documentation/
- **Pandas**: https://pandas.pydata.org/docs/
- **Scikit-learn**: https://scikit-learn.org/

### Docker
- **Docker Documentation**: https://docs.docker.com/
- **Docker Compose**: https://docs.docker.com/compose/

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Hacer fork del repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

---

## 📝 Changelog

### v1.0.0 (Actual)
- ✅ Implementado Loader (PASO 1)
- ✅ Implementada Extracción de Subgrafos (PASO 2)
- 🔮 Extracción de Scores (PASO 3)
- 🔮 Extracción de Métricas (PASO 4)
- 🔮 Propiedades (PASO 5)
- 🔮 Visualización (PASO 6)

---

## 👨‍💻 Autor

**Cristian Morales Navarro**  
📧 Email: [tu_email@ejemplo.com]  
🔗 GitHub: [tu_github_url]  
🏆 Trabajo de Fin de Máster - MUSII  
🎓 Universidad de Alcalá

---

## 📞 Soporte

Para reportar bugs o sugerencias:

1. **Abrir un Issue** en GitHub
2. **Describir el problema** detalladamente
3. **Incluir logs** y pasos para reproducir
4. **Contactar directamente** si es urgente

---

## 📄 Licencia

Este proyecto está bajo licencia [MIT / Apache 2.0 / Tu Licencia].

Usa el código libremente para propósitos educativos y de investigación.

---

## 📊 Descripción Detallada de cada Módulo

### 1. **Loader - Carga de Bases de Datos** (`arquitectura_completa/`)

**Propósito:** Crear e inicializar las bases de datos Neo4j con datos de usuarios, hoteles e interacciones.

**Procesos:**
- Crea dos bases de datos: `interactions` y `knowledge`
- Carga CSV de interacciones usuario-hotel con ratings
- Construye grafo de conocimiento con propiedades de hoteles

**Entrada:**
- `grafo_interaccion_datos_train.csv`: user_id, business_id, rating
- `grafo_conocimiento_datos_hoteles.csv`: item_id, name, city, state, latitude, longitude, stars, review_count, category, etc.

**Salida:**
- Neo4j con dos bases de datos activas y datos cargados

**Documentación:** Ver [arquitectura_completa/README.md](arquitectura_completa/README.md)

---

### 2. **Extracción de Subgrafos** (`extraccion_subgrafo/`)

**Propósito:** Extraer subgrafos personalizados que conectan usuarios con hoteles recomendados para explicabilidad.

**Procesos:**
- Obtiene historial de hoteles de cada usuario
- Extrae subgrafo del conocimiento que incluye el hotel recomendado + histórico
- Genera subgrafos completos con todas las interacciones del usuario

**Entrada:**
- Bases de datos Neo4j inicializadas
- CSV con pares (usuario, hotel_recomendado)

**Salida:**
- Archivos JSON con subgrafos (formato: nodos + relaciones)
- Dos tipos: individuales por recomendación y completos por usuario

**Archivos generados:**
- `data/subgrafos/user_X_hotel_Y.json` (individual)
- `data/subgrafos_completos/user_X_full_subgraph.json` (completo)

**Documentación:** Ver [extraccion_subgrafo/README.md](extraccion_subgrafo/README.md)

---

### 3. **Extracción de Scores** (`extraccion_scores/`) - 🔮 En desarrollo

**Propósito:** Calcular métricas básicas y scores de recomendación.

**Procesos esperados:**
- Calcular cobertura de recomendaciones
- Generar scores básicos
- Pipeline de procesamiento

**Entrada:** Subgrafos JSON

**Salida:** CSVs con scores y métricas básicas

---

### 4. **Extracción de Métricas** (`extraccion_métricas/`) - 📊 En desarrollo

**Propósito:** Análisis profundo con múltiples métricas de explicabilidad.

**Métricas disponibles:**
- Centralidad (betweenness, closeness, degree)
- Cobertura
- Diversidad
- Novedad
- Similitud
- Rutas de recomendación
- Popularidad
- Ejemplos

**Salida:** CSVs detallados en `csv_explicabilidad/`

---

### 5. **Extracción de Propiedades** (`extraccion_prop/`) - 🔧 En desarrollo

**Propósito:** Procesar y extraer propiedades específicas de hoteles.

---

### 6. **Visualizador de Métricas** (`visualizador_metricas/`) - 📈 En desarrollo

**Propósito:** Crear visualizaciones interactivas de resultados y explicaciones.

**Salida esperada:** Dashboards y gráficos interactivos

---

## 🔧 Troubleshooting

### Neo4j no inicia
```bash
# Verificar logs del contenedor
---

## 🔄 Ejemplos de Consultas Cypher

### Base `interactions`

Usuarios más activos:
```cypher
:use interactions
MATCH (u:User)-[r:RATED]->(b:Business)
RETURN u.id AS user_id, COUNT(r) AS total_ratings
ORDER BY total_ratings DESC
LIMIT 10;
```

Hoteles más valorados:
```cypher
MATCH (u:User)-[r:RATED]->(b:Business)
RETURN b.id AS business_id, COUNT(r) AS rating_count, AVG(r.rating) AS avg_rating
ORDER BY rating_count DESC
LIMIT 10;
```

Valoraciones altas:
```cypher
MATCH (u:User)-[r:RATED]->(b:Business)
WHERE r.rating > 4
RETURN u.id AS user_id, b.id AS business_id, r.rating
ORDER BY r.rating DESC
LIMIT 20;
```

### Base `knowledge`

Hoteles por ciudad:
```cypher
:use knowledge
MATCH (b:Business)-[r:RELATION {type:"located_in_city"}]->(c:Node)
RETURN c.name AS city, COUNT(b) AS business_count
ORDER BY business_count DESC
LIMIT 10;
```

Categorías más comunes:
```cypher
MATCH (b:Business)-[r:RELATION {type:"has_category"}]->(cat:Node)
RETURN cat.name AS category, COUNT(b) AS business_count
ORDER BY business_count DESC
LIMIT 10;
```

Hoteles por rating:
```cypher
MATCH (b:Business)-[r:RELATION {type:"has_rating"}]->(n:Node)
WITH b, toFloat(split(n.name,' ')[0]) AS stars
RETURN b.id AS business_id, stars
ORDER BY stars DESC
LIMIT 10;
```

---

## 💡 Casos de Uso

### Caso 1: Recomendar hotel a usuario existente

```
1. Usuario 3 ha visitado: [hotel 104, 1054, 1093, ...]
2. Sistema recomienda: hotel 2963
3. Módulo extraccion_subgrafo extrae relaciones comunes
4. Módulo extraccion_métricas analiza por qué es buena recomendación
5. Resultado: Usuario ve "Hotel 2963 recomendado porque:"
              "- Ubicado en Madrid (como tus hoteles previos)"
              "- Categoría Hotels/Budget (coincide con preferencias)"
              "- Rating 4.5 (similar a tus ratings previos)"
```

### Caso 2: Analizar explicabilidad de recomendaciones

```
1. Procesar todas las recomendaciones del sistema
2. Calcular métricas para cada una
3. Identificar recomendaciones con baja explicabilidad
4. Mejorar argumentos o modelo de recomendación
5. Visualizar resultados en dashboard
```

### Caso 3: Comparar usuarios similares

```
1. Usuario A y Usuario B han dado ratings a hoteles similares
2. Extraer subgrafos de ambos usuarios
3. Comparar propiedades en los subgrafos
4. Encontrar hoteles de A que podrían gustar a B
```

---

## 📊 Métricas y KPIs

### Métricas de Cobertura
- **Coverage**: % de propiedades del hotel incluidas en el subgrafo
- **Precision**: % de propiedades relevantes vs total de propiedades
- **Recall**: % de propiedades importantes que se muestran

### Métricas de Explicabilidad
- **Centralidad**: Importancia de nodos en el subgrafo
- **Diversidad**: Variedad de tipos de propiedades
- **Novedad**: Qué tan nuevo es el hotel para el usuario
- **Similitud**: Parecido con historial del usuario

### Métricas de Calidad
- **Precisión**: % de recomendaciones que el usuario encuentra útiles
- **Recall**: % de hoteles útiles que son recomendados
- **F1-Score**: Promedio armónico de precisión y recall

---

## 🔐 Seguridad y Mejores Prácticas

### Cambiar Contraseña de Neo4j (Producción)

```bash
# En docker-compose.yml, cambiar:
NEO4J_ADMIN_PASSWORD=tu_password_fuerte_aqui

# Luego:
docker-compose down -v
docker-compose up --build
```

### Limitaciones de Recursos

```yaml
# docker-compose.yml
services:
  neo4j:
    mem_limit: 4g
    memswap_limit: 4g
    cpus: '2.0'
```

### Backups Automáticos

```bash
#!/bin/bash
# backup_neo4j.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker exec neo4j neo4j-admin dump \
  --database=interactions \
  --to=/backup/interactions_$DATE.dump
docker exec neo4j neo4j-admin dump \
  --database=knowledge \
  --to=/backup/knowledge_$DATE.dump
```

---

## 🚀 Optimizaciones Futuras

- [ ] Paralelizar extracción de subgrafos
- [ ] Cachear resultados de métricas
- [ ] Implementar recomendaciones en tiempo real
- [ ] Agregar visualización con D3.js
- [ ] Exportar reportes PDF
- [ ] API REST para recomendaciones
- [ ] Dashboard web interactivo
- [ ] Modelos de ML para ranking

---

## 📖 Documentación Adicional

Cada módulo tiene su propia documentación:

- [arquitectura_completa/README.md](arquitectura_completa/README.md) - Carga de datos
- [extraccion_subgrafo/README.md](extraccion_subgrafo/README.md) - Extracción de subgrafos
- [extraccion_métricas/README_METRICAS.md](extraccion_métricas/README_METRICAS.md) - Detalle de métricas

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Hacer fork del repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

---

## 📝 Changelog

### v1.0.0 (Actual)
- ✅ Implementado Loader (PASO 1) - Carga de Neo4j
- ✅ Implementada Extracción de Subgrafos (PASO 2)
- 🔮 Extracción de Scores (PASO 3) - En desarrollo
- 🔮 Extracción de Métricas (PASO 4) - Parcialmente hecho
- 🔮 Propiedades (PASO 5) - En desarrollo
- 🔮 Visualización (PASO 6) - En desarrollo

---

## 👨‍💻 Autor y Contacto

**Cristian Morales Navarro**  
📧 Email: [tu_email@ejemplo.com]  
🔗 GitHub: [tu_github_url]  
🏆 Trabajo de Fin de Máster - MUSII  
🎓 Universidad de Alcalá  
📅 Año: 2025-2026

---

## 📄 Licencia

Este proyecto está bajo licencia [MIT / Apache 2.0 / Tu Licencia].

Usa el código libremente para propósitos educativos y de investigación.

---

## 🙏 Agradecimientos

- Supervisor/a del TFM por orientación y feedback
- Equipo MUSII por recursos y soporte
- Comunidad de Neo4j y Python por excelentes herramientas

---

**¡Gracias por usar este sistema! 🚀**


