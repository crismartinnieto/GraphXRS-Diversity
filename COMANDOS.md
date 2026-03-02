COMANDOS



**#LEVANTAR CONTENEDOR**

cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\docker

docker-compose up --build



**#EXTRAER Y CALCULAR METRICAS DE GRAFO CONOCIMIENTO**

cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_subgrafos\\subgrafo\_conocimiento

python src/extraccion\_subgrafos/subgrafo\_conocimiento/main\_user\_subgraph.py



cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_explicaciones\_conocimiento

python src/extraccion\_explicaciones\_conocimiento/crear\_explicaciones.py



**#EXTRAER Y CALCULAR METRICAS DE GRAFO INTERACCION**

cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_subgrafos\\subgrafo\_interaccion

python src/extraccion\_subgrafos/subgrafo\_interaccion/extract\_interaction\_subgraphs.py



\# 

cd .\\Desktop\\MUSII\\TFM\\nueva\_estructura\\src\\extraccion\_metricas\_conocimiento

python src/extraccion\_metricas\_conjunto/xaigraph.py



