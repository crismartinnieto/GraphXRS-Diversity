# Sistema_recomendacion_xai_TFM_MUSII_CMN

## Carga de datos en Neo4j para hoteles

Este proyecto contiene una arquitectura completa para cargar y gestionar información de usuarios y hoteles en **Neo4j** utilizando **Docker Compose**.  
Incluye dos bases de datos: `interactions` (interacciones usuarios-negocios) y `knowledge` (grafo de conocimiento de hoteles).

---

## 📂 Estructura del proyecto

```

arquitectura_completa/
│
├─ docker-compose.yml         # Configuración de los servicios Docker: Neo4j y loader
│
├─ loader/                    # Servicio para cargar datos en Neo4j
│   ├─ Dockerfile             # Imagen para el loader de datos
│   ├─ requirements.txt       # Dependencias Python
│   ├─ load_databases.py      # Script que crea bases de datos y carga CSVs en Neo4j
│   └─ data/                  # Carpeta con los CSVs a cargar
│       ├─ grafo_conocimiento_datos_hoteles.csv
│       └─ grafo_interaccion_datos_train.csv
│
└─ volumes/
└─ neo4j_data             # Volumen persistente para Neo4j

````


---

## 🛠 Requisitos

- Docker >= 24.0  
- Docker Compose >= 2.0  
- Python 3.11+ (para el loader, aunque se ejecuta dentro del contenedor)

---

## ⚡ Cómo desplegar

1. Clonar el repositorio:

```bash
git clone <TU_REPOSITORIO>
cd arquitectura_completa

Perfecto, aquí tienes **el README completo listo para copiar y pegar tal cual en un fichero `README.md`**. Todo el contenido está unificado y formateado:

---

```markdown
# Sistema_recomendacion_xai_TFM_MUSII_CMN

## Carga de datos en Neo4j para hoteles

Este proyecto contiene una arquitectura completa para cargar y gestionar información de usuarios y hoteles en **Neo4j** utilizando **Docker Compose**.  
Incluye dos bases de datos: `interactions` (interacciones usuarios-negocios) y `knowledge` (grafo de conocimiento de hoteles).

---

## 🛠 Requisitos

- Docker >= 24.0  
- Docker Compose >= 2.0  
- Python 3.11+ (para el loader, aunque se ejecuta dentro del contenedor)

---

## ⚡ Cómo desplegar

1. Clonar el repositorio:

```bash
git clone <TU_REPOSITORIO>
cd arquitectura_completa
````

2. Construir y levantar los servicios:

```bash
docker-compose up --build
```

Esto hará:

* Levantar un contenedor Neo4j Enterprise (`neo4j-hoteles`) accesible en:

  * **Neo4j Browser:** `http://localhost:7474`
  * **Bolt:** `bolt://localhost:7687`
    
* Ejecutar el contenedor `neo4j-loader` que:

  * Crea las bases `interactions` y `knowledge`
  * Carga los CSVs en Neo4j
  * Inserta nodos y relaciones según la lógica definida en `load_databases.py`

3. Verificar que Neo4j está corriendo:

```bash
docker ps
```

* Contenedor `neo4j-hoteles` en ejecución
* Contenedor `neo4j-loader` se cerrará automáticamente tras cargar los datos

---

## 🔹 Uso de Neo4j

* Usuario: `neo4j`
* Contraseña: `test12345`

Puedes acceder al **Neo4j Browser** en `http://localhost:7474` y ejecutar consultas Cypher.

Ejemplos:

```cypher
MATCH (u:User)-[r:RATED]->(b:Business)
RETURN u.id, b.id, r.rating
LIMIT 10;

MATCH (b:Business)-[r:RELATION {type:"located_in_city"}]->(c:Node)
RETURN b.id, c.name
LIMIT 10;
```

---

## 📝 Descripción de cada fichero

| Fichero                                            | Descripción                                                                                        |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `docker-compose.yml`                               | Orquesta los servicios Neo4j y loader, define puertos, volúmenes y dependencias.                   |
| `loader/Dockerfile`                                | Imagen Docker para ejecutar Python y el script de carga.                                           |
| `loader/requirements.txt`                          | Dependencias Python necesarias (`pandas`, `py2neo`, etc.)                                          |
| `loader/load_databases.py`                         | Script principal: crea bases de datos, elimina nodos existentes, carga CSVs y genera relaciones.   |
| `loader/data/grafo_interaccion_datos_train.csv`    | CSV con interacciones usuario-negocio (ratings).                                                   |
| `loader/data/grafo_conocimiento_datos_hoteles.csv` | CSV con información de hoteles (nombre, ciudad, categoría, coordenadas, estrellas, reviews, etc.). |
| `volumes/neo4j_data`                               | Volumen persistente de Neo4j para mantener la base de datos entre reinicios.                       |

---

## 🔧 Notas adicionales

* Los volúmenes Docker aseguran que los datos no se pierdan al detener el contenedor.
* El script `load_databases.py` espera unos segundos para que Neo4j esté listo antes de cargar los datos.
* Si quieres recargar los datos, elimina los nodos y relaciones existentes o borra el volumen:

```bash
docker-compose down -v
docker-compose up --build
```
