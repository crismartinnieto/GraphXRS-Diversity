# Sistema de explicaciones post-hoc basado en grafos de conocimiento para sistemas de recomendación externos

Repositorio asociado al Trabajo Fin de Máster **Sistema de Explicaciones Post-hoc basado en Grafos de Conocimiento para Sistemas de Recomendación Externos** (Máster en Sistemas Interactivos Inteligentes, UAM).

El proyecto implementa un *framework* modular y agnóstico al recomendador. A partir de recomendaciones externas, genera explicaciones basadas en ejemplos del historial del usuario mediante dos fuentes complementarias:

- **Grafo de conocimiento (KG):** identifica similitudes semánticas entre el hotel recomendado y los hoteles del historial del usuario.
- **Grafo de interacción (CF):** identifica patrones colaborativos entre el usuario objetivo, otros usuarios y hoteles valorados en común.

Después, evalúa la diversidad de los explicadores obtenidos con las métricas AggDiv, IXD, MIL y ECS.

## Flujo del *framework*

1. Se cargan en Neo4j las interacciones históricas y las propiedades semánticas de los hoteles.
2. Un recomendador externo proporciona los pares usuario–hotel que se desean explicar.
3. Para cada par se extraen un subgrafo de conocimiento y un subgrafo de interacción personalizados.
4. Se puntúan los hoteles del historial que pueden actuar como explicadores mediante cuatro algoritmos KG y cuatro CF.
5. Se evalúa la diversidad explicativa de los resultados por usuario, sistema e ítem recomendado.

## Estructura del repositorio

```text
.
├── README.md
├── COMANDOS.md
├── data/
│   ├── raw/                              # Datos de entrada para Neo4j
│   └── recomendaciones_del_modelo/       # Rankings generados externamente
├── docker/
│   ├── docker-compose.yml
│   └── loader/                           # Carga de los grafos en Neo4j
├── logs/                                 # Registros de ejecución
├── output/                               # Resultados y artefactos de depuración
└── src/
    ├── extraccion_subgrafos/             # Consultas y extracción de subgrafos
    ├── extraccion_algoritmos/            # Puntuación de explicadores KG y CF
    ├── evaluacion/                       # Marco de diversidad explicativa
    └── visualizacion/                    # Notebooks de análisis y tablas
```

## Datos de entrada

Antes de ejecutar el proyecto, `data/raw/` debe contener los siguientes archivos:

| Archivo | Finalidad | Columnas necesarias |
| --- | --- | --- |
| `grafo_interaccion_datos_train.csv` | Histórico de valoraciones para el grafo de interacción. | `user_id`, `business_id`, `rating` |
| `grafo_conocimiento_datos_hoteles.csv` | Propiedades de los hoteles para el grafo de conocimiento. | `item_id`, `name`, `city`, `state`, `postal_code`, `latitude`, `longitude`, `stars`, `review_count`, `is_open`, `category`, `attribute_key`, `attribute_value` |

En `data/recomendaciones_del_modelo/` deben ubicarse los CSV de recomendaciones que se quieren explicar. El nombre debe ajustarse al patrón `relacion_usuario_rating_recomendador*.csv` e incluir, como mínimo, las columnas `usuario` y `negocio`.

## Componentes principales

### Carga de grafos

`docker/loader/load_databases.py` crea dos bases de datos en Neo4j:

- `interactions`, con nodos `:User` y `:Business` unidos por relaciones `:RATED`.
- `knowledge`, con nodos `:Business` y `:Node` unidos por relaciones `:RELATION` que representan propiedades semánticas.

### Generación de explicaciones

`src/extraccion_algoritmos/pipeline.py` procesa los rankings externos. Para cada recomendación, obtiene los subgrafos locales y genera un ranking de hoteles explicadores.

La familia KG aplica las métricas `kg_num_propiedades_compartidas`, `kg_ratio_propiedades_compartidas`, `kg_peso_ponderado_perfil` y `kg_jaccard_similarity`. La familia CF aplica `cf_degree_hotel`, `cf_ratio_usuarios_compartidos`, `cf_norm_degree_hotel` y `cf_betweenness_hotel`.

### Evaluación de diversidad explicativa

`src/evaluacion/pipeline.py` calcula:

- **AggDiv:** amplitud del vocabulario explicativo por usuario.
- **IXD:** heterogeneidad de las explicaciones de las distintas recomendaciones de un usuario.
- **MIL:** personalización de las listas de explicadores entre usuarios.
- **ECS:** consistencia de las explicaciones asociadas a un mismo hotel recomendado.

Los notebooks de `src/visualizacion/` permiten analizar distribuciones y generar tablas comparativas de estas métricas.

## Ejecución

Consulta [COMANDOS.md](COMANDOS.md) para el procedimiento completo. El orden de ejecución es el siguiente:

1. Levantar Neo4j y cargar los grafos.
2. Generar explicaciones para las recomendaciones externas.
3. Evaluar la diversidad explicativa.
4. Analizar los CSV resultantes en los notebooks.

## Salidas

El pipeline de generación guarda los resultados por recomendador y fuente en:

- `output/<modelo>/metricas_grafo_conocimiento_<modo>/`
- `output/<modelo>/metricas_grafo_interaccion_<modo>/`

El pipeline de evaluación genera los resultados en `output/<modelo>/metricas_evaluacion_<modo>/`. Con `--debug`, también se crean en `output/debug/` los subgrafos extraídos y los informes de validación.

## Observaciones

- El *framework* no entrena ni modifica el recomendador base: recibe sus recomendaciones como entrada y las explica de forma post-hoc.
- Los grafos de interacción se construyen a partir de entrenamiento para evitar filtración de información futura.
