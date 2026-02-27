COMANDOS



**#LEVANTAR CONTENEDOR**

cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\docker

docker-compose up --build



**#EXTRAER Y CALCULAR METRICAS DE GRAFO CONOCIMIENTO**

cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_subgrafos\\subgrafo\_conocimiento

python main\_user\_subgraph.py



cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_explicaciones\_conocimiento

python crear\_explicaciones.py



cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_metricas\_conocimiento

python calcular.py



**#EXTRAER Y CALCULAR METRICAS DE GRAFO INTERACCION**

cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_subgrafos\\subgrafo\_interaccion

python .\\extract\_interaction\_subgraphs.py



cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_metricas\_interaccion

python .\\calcular.py



