# Guía de ejecución

Ejecuta los comandos desde la raíz del repositorio.

## 1. Preparar los datos

Comprueba que existen los archivos siguientes:

```text
data/raw/grafo_interaccion_datos_train.csv
data/raw/grafo_conocimiento_datos_hoteles.csv
data/recomendaciones_del_modelo/relacion_usuario_rating_recomendador*.csv
```

Los CSV de recomendaciones deben contener las columnas `usuario` y `negocio`.

## 2. Levantar Neo4j y cargar los grafos

```bash
cd docker
docker-compose up --build
```

Este paso inicia Neo4j y carga el grafo de interacción y el grafo de conocimiento a partir de los datos de `data/raw/`.

Cuando finalice la carga, vuelve a la raíz del repositorio:

```bash
cd ..
```

## 3. Generar explicaciones post-hoc

Procesar una muestra de usuarios:

```bash
python src/extraccion_algoritmos/pipeline.py --modo muestra
```

Opciones habituales:

```bash
# Elegir usuarios concretos en modo muestra
python src/extraccion_algoritmos/pipeline.py --modo muestra --usuarios 3 35

# Procesar las primeras cinco recomendaciones de cada usuario
python src/extraccion_algoritmos/pipeline.py --modo semi

# Procesar todas las recomendaciones disponibles
python src/extraccion_algoritmos/pipeline.py --modo completo

# Generar artefactos para validar un hotel recomendado concreto
python src/extraccion_algoritmos/pipeline.py --modo muestra --debug --hotel 45

# Procesar un único CSV de recomendaciones
python src/extraccion_algoritmos/pipeline.py --modo muestra --csv-recomendaciones ruta/al/archivo.csv
```

## 4. Evaluar la diversidad explicativa

```bash
python src/evaluacion/pipeline.py --modo muestra --fuente kg cf
```

Opciones habituales:

```bash
# Definir los cortes top-k
python src/evaluacion/pipeline.py --modo completo --ks 1 3 5

# Evaluar únicamente la familia de algoritmos KG o CF
python src/evaluacion/pipeline.py --modo semi --fuente kg
python src/evaluacion/pipeline.py --modo semi --fuente cf

# Evaluar modelos recomendadores concretos
python src/evaluacion/pipeline.py --modo completo --modelo FunkSVD ItemKNN

# Exigir un mínimo de usuarios por hotel para ECS
python src/evaluacion/pipeline.py --modo completo --ecs-min-usuarios 2
```

## 5. Consultar los resultados

- Los resultados de puntuación KG y CF se guardan en `output/<modelo>/`.
- Los resultados de AggDiv, IXD, MIL y ECS se guardan en `output/<modelo>/metricas_evaluacion_<modo>/`.
- Los registros de ejecución se encuentran en `logs/`.
- Los notebooks de `src/visualizacion/` se usan para elaborar las gráficas y tablas del análisis experimental.
