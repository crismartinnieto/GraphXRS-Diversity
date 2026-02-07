# Extracción de Subgrafos - Subgraph Extraction

Este módulo se encarga de **extraer subgrafos personalizados** a partir del grafo de conocimiento en **Neo4j**, conectando usuarios con hoteles recomendados y sus relaciones dentro de un sistema de recomendación **XAI**.

---

## 📋 Descripción

El módulo permite:

- **Extracción de subgrafos usuario–hotel**  
  Crea grafos que combinan las interacciones previas de un usuario con un hotel recomendado.

- **Extracción de subgrafos completos por usuario**  
  Genera grafos que incluyen todos los hoteles con los que un usuario ha interactuado.

- **Persistencia en JSON**  
  Guarda los subgrafos extraídos en formato JSON para análisis y visualización posterior.

---

## 📁 Estructura

```text
extraccion_subgrafo/
├── main_user_subgraph.py           # Extrae subgrafos usuario-hotel individuales
├── main_user_full_subgraph.py      # Extrae subgrafos completos por usuario
├── utils_interactions.py           # Utilidades para consultar interacciones usuario-hotel
├── utils_knowledge.py              # Utilidades para extraer del grafo de conocimiento
├── save_graph.py                   # Funciones para guardar subgrafos en JSON
├── requirements.txt                # Dependencias
└── data/
    ├── subgrafos/                  # Subgrafos usuario-hotel individuales
    │   ├── user_3_hotel_104.json
    │   ├── user_3_hotel_1054.json
    │   └── ...
    └── subgrafos_completos/        # Subgrafos completos por usuario
        ├── user_3_full_subgraph.json
        ├── user_35_full_subgraph.json
        └── ...
````

---

## 🔧 Requisitos

* Neo4j ejecutándose con las bases de datos `interactions` y `knowledge` cargadas
* Python 3.8+
* Dependencias:

  * `py2neo`
  * `networkx`
  * `matplotlib`

---

## 🚀 Uso

### 🔹 Extracción individual usuario–hotel

Desde código:

```python
from main_user_subgraph import extract_user_subgraph

# Extraer subgrafo para el usuario 3 con hotel recomendado 2963
extract_user_subgraph(user_id=3, recommended_hotel=2963)
```

O desde línea de comandos para procesar un CSV:

```bash
python main_user_subgraph.py
```

---

### 🔹 Extracción de subgrafo completo por usuario

Desde código:

```python
from main_user_full_subgraph import extract_user_full_subgraph

# Extraer todos los hoteles con los que ha interactuado el usuario 3
extract_user_full_subgraph(user_id=3)
```

---

## 📊 Componentes

### `utils_interactions.py`

Conecta a la base `interactions` y obtiene los hoteles con los que un usuario ha interactuado.

* `get_user_interacted_hotels(user_id)`
  Retorna una lista de IDs de hoteles.

---

### `utils_knowledge.py`

Conecta a la base `knowledge` y extrae subgrafos del grafo de conocimiento.

* `get_knowledge_graph()`
  Establece conexión con Neo4j.

* `get_subgraph_for_hotels(hotel_ids)`
  Extrae nodos y relaciones para un conjunto específico de hoteles.

---

### `save_graph.py`

Persiste los subgrafos extraídos en formato JSON.

* `save_subgraph_to_json(nodes, relationships, filename)`
  Guarda el subgrafo en `data/subgrafos/`.

---

## 🔄 Flujo de Ejecución

1. **Consulta interacciones**
   Obtiene el historial de hoteles del usuario desde la base `interactions`.

2. **Combina hoteles**
   Une el hotel recomendado con los hoteles previamente visitados por el usuario.

3. **Extrae subgrafo**
   Recupera nodos y relaciones desde el grafo de conocimiento.

4. **Guarda JSON**
   Persiste el subgrafo en un archivo JSON para análisis y visualización.

---

## 📝 Entrada de Datos

El módulo espera un archivo CSV con las siguientes columnas:

* `user_id`
* `recommended_hotel` (o equivalente)

Ejemplo:

```text
relacion_usuario_rating_recomendador.csv
```

---

## 📤 Salida

Subgrafos almacenados en formato JSON con la siguiente estructura:

```json
{
  "nodes": [
    {
      "id": "hotel_1",
      "label": "Business",
      "properties": { }
    },
    {
      "id": "attr_1",
      "label": "Node",
      "properties": { }
    }
  ],
  "relationships": [
    {
      "source": "hotel_1",
      "target": "attr_1",
      "type": "has_category"
    }
  ]
}
```


