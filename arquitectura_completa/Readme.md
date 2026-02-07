## Loader - Carga de Bases de Datos Neo4j

Este módulo es responsable de inicializar y cargar datos en **Neo4j** para un sistema de recomendación **XAI** basado en **grafos de conocimiento e interacciones**.


## 📋 Descripción

El loader automatiza el proceso de:

- Crear bases de datos en Neo4j (`interactions` y `knowledge`)
- Cargar datos de interacciones **usuario–hotel** con ratings
- Construir un **grafo de conocimiento** con propiedades de hoteles (ubicación, categorías, atributos, etc.)


## 📁 Estructura

```text
loader/
├── Dockerfile              # Imagen Docker del loader
├── load_databases.py       # Script principal de carga
├── requirements.txt        # Dependencias Python
└── data/
    ├── grafo_interaccion_datos_train.csv      # Datos de interacciones
    └── grafo_conocimiento_datos_hoteles.csv   # Datos de hoteles
````


## 🔧 Requisitos

* Docker y Docker Compose
* Neo4j ejecutándose (configurado en `docker-compose.yml`)
* Python 3.8+ (si se ejecuta localmente)

### Dependencias Python

* `pandas`
* `py2neo`



## 🚀 Uso

### Con Docker Compose

Este proceso:

* Inicia una instancia de Neo4j
* Ejecuta automáticamente el loader para cargar ambas bases de datos
* Espera a que Neo4j esté listo antes de proceder (sleep inicial)


## ⚙️ Configuración

Las variables de entorno se pueden personalizar:

```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test12345
```


## 📊 Bases de Datos Cargadas

### 🗂️ Base `interactions`

Almacena las relaciones usuario–hotel con ratings:

* **Nodos**: `User`, `Business`
* **Relación**:
  `User -[RATED]-> Business` (con propiedad `rating`)

---

### 🧠 Base `knowledge`

Grafo de conocimiento con propiedades de hoteles.

**Propiedades incluidas:**

* Nombre: `has_name`
* Ubicación:

  * Ciudad: `located_in_city`
  * Estado: `in_state`
  * Código postal: `has_postal_code`
* Coordenadas geográficas: `has_coordinates`
* Calificación y número de reviews:

  * `has_rating`
  * `has_review_count`
* Estado del negocio (abierto/cerrado)
* Categorías: `has_category`
* Atributos personalizados: `has_attribute`


## 📈 Datos de Entrada

El script espera archivos CSV en el directorio `data/`:

* **grafo_interaccion_datos_train.csv**
  Columnas: `user_id`, `business_id`, `rating`

* **grafo_conocimiento_datos_hoteles.csv**
  Información completa de hoteles y sus propiedades


## ✅ Logs

El script genera logs detallados con emojis para facilitar el seguimiento:

* ✅ Operaciones exitosas
* ⚠️ Advertencias
* 🔹 Información
* 📊 Resumen final

