# Spark Standalone con GPU (RAPIDS) - Streaming de Eventos de Fútbol

Proyecto de procesamiento de datos en tiempo real usando Apache Spark con aceleración GPU (NVIDIA RAPIDS), Kafka, y datos 360 de StatsBomb para Liga MX.

## Arquitectura del Proyecto

### Arquitectura 1: Spark Standalone con GPU (NVIDIA + RAPIDS) ⚡
- **Objetivo:** Procesamiento de alta velocidad (4096+ eventos/seg) con aceleración GPU
- **Componentes:** Spark Master + Worker con GPU, RAPIDS SQL Plugin habilitado
- **Ventaja:** Rendimiento optimizado para operaciones de DataFrame y ML

### Arquitectura 2: Spark Standalone CPU (para comparación)
- **Objetivo:** Baseline de rendimiento sin GPU
- **Configuración:** Mismo código, RAPIDS plugin deshabilitado
- **Propósito:** Comparar métricas GPU vs CPU

## Estructura del Proyecto

```
final2/
├── docker-compose.yml           # Orquestación de 6 servicios
├── .env.example                 # Template de variables de entorno
├── data/                        # Datos de StatsBomb (persistente)
├── models/                      # Modelos ML entrenados
├── notebooks/                   # Jupyter notebooks
│   ├── 02_Entrenamiento_Modelo_LWP.ipynb
│   ├── 03_Streaming_Estadisticas.ipynb
│   └── 04_Streaming_Inferencia_LWP.ipynb
├── producer/                    # Productor de Kafka
│   ├── Dockerfile
│   ├── producer.py
│   └── requirements.txt
├── jupyter/                     # Jupyter Lab con GPU
│   ├── Dockerfile
│   └── requirements.txt
├── spark-rapids/                # Custom Spark + RAPIDS image
│   └── Dockerfile
└── spark-conf/                  # Configuración de Spark
    └── spark-defaults.conf
```

## Requisitos

### Hardware
- **GPU:** NVIDIA GPU con soporte CUDA 11.8 o superior
- **RAM:** Mínimo 16GB recomendado
- **CPU:** 8+ cores recomendado
- **Disco:** 50GB+ espacio libre

### Software
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit (nvidia-docker2)
- NVIDIA Driver 470+ (compatible con CUDA 11.8)

### Componentes de la Imagen Custom
- **Base:** nvidia/cuda:11.8.0-runtime-ubuntu22.04
- **Spark:** Apache Spark 3.3.1
- **RAPIDS Accelerator:** v23.12.2 (rapids-4-spark_2.12-23.12.2.jar)
- **Java:** OpenJDK 11
- **Python:** 3.10

### Verificar GPU en Docker
```bash
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## Configuración Inicial

### 1. Clonar y Configurar Credenciales

```bash
# Copiar template de variables de entorno
cp .env.example .env

# Editar con tus credenciales de StatsBomb
nano .env
```

Actualiza las siguientes variables en `.env`:
```bash
STATSBOMB_USER=tu_usuario
STATSBOMB_PASSWORD=tu_contraseña
```

### 2. Construir y Levantar Servicios

```bash
# Construir imágenes
docker-compose build

# Levantar todos los servicios
docker-compose up -d

# Verificar que todos los servicios están corriendo
docker-compose ps
```

**Servicios disponibles:**
- `zookeeper` - Puerto 2181
- `kafka` - Puertos 9092 (interno), 9093 (externo)
- `producer` - Simulador de eventos
- `spark-master` - Puerto 8080 (Web UI), 7077 (Master)
- `spark-worker` - Puerto 8081 (Web UI)
- `jupyter-lab` - Puerto 8888

### 3. Acceder a Jupyter Lab

```bash
# Abrir en navegador
http://localhost:8888

# No requiere token (deshabilitado para desarrollo)
```

### 4. Verificar Kafka

```bash
# Ver logs del productor
docker-compose logs -f producer

# Deberías ver: "Throughput: 4096+ events/sec"
```

## Flujo de Trabajo

### Paso 1: Entrenar Modelo de Live Win Probability (LWP)

Abrir notebook: `notebooks/02_Entrenamiento_Modelo_LWP.ipynb`

**Objetivos:**
- Cargar 4 temporadas de datos históricos de Liga MX
- Feature engineering con datos 360
- Entrenar modelo Random Forest para predecir resultado
- Guardar modelo en `/work/models/lwp_model`

**Métricas a observar:**
- Accuracy del modelo
- F1 Score
- Training time (GPU vs CPU)
- Feature importance

**Spark UI:** http://localhost:4040

### Paso 2: Streaming de Estadísticas en Tiempo Real

Abrir notebook: `notebooks/03_Streaming_Estadisticas.ipynb`

**Objetivos:**
- Consumir stream de Kafka (4096+ eventos/seg)
- Calcular estadísticas en ventanas de 1 minuto:
  - Mínimos, máximos, promedios, varianza
  - Pases, distancia, posiciones, posesión
- Output a consola

**Métricas a capturar desde Spark UI:**
- Input Rate (eventos/segundo)
- Process Rate (eventos/segundo)
- Batch Duration
- Scheduling Delay
- Shuffle Read/Write
- Spill (Memory/Disk)

### Paso 3: Inferencia de ML en Streaming

Abrir notebook: `notebooks/04_Streaming_Inferencia_LWP.ipynb`

**Objetivos:**
- Cargar modelo LWP entrenado
- Aplicar modelo al stream en vivo
- Predecir probabilidades de victoria en tiempo real:
  - P(Victoria Local)
  - P(Empate)
  - P(Victoria Visitante)

**Métricas adicionales:**
- ML inference overhead
- Latencia por batch (con vs sin ML)
- GPU utilization durante inferencia

## Captura de Métricas (Spark UI)

### Acceder a Spark UI
```
http://localhost:4040
```

### Métricas Clave para Comparación GPU vs CPU

#### Tab: Streaming
- ✓ Input Rate
- ✓ Process Rate
- ✓ Batch Duration
- ✓ Operation Duration
- ✓ Scheduling Delay

#### Tab: Jobs
- ✓ Job Duration
- ✓ Shuffle Read
- ✓ Shuffle Write
- ✓ Spill (Memory)
- ✓ Spill (Disk)

#### Tab: Stages
- ✓ Stage Duration
- ✓ GC Time
- ✓ Task Metrics

#### Tab: Executors
- ✓ Memory Used
- ✓ Disk Used
- ✓ Total Tasks
- ✓ Task Time

## Cambiar a Arquitectura 2 (CPU)

Para comparar rendimiento sin GPU:

### 1. Deshabilitar RAPIDS Plugin

Editar `spark-conf/spark-defaults.conf`:

```bash
# Comentar estas líneas:
# spark.plugins                           com.nvidia.spark.SQLPlugin
# spark.rapids.sql.enabled                true
# spark.rapids.sql.explain                ALL
# spark.rapids.memory.pinnedPool.size     2G
```

### 2. Remover Asignación de GPU

Editar `docker-compose.yml` y comentar/eliminar estas secciones en `spark-master`, `spark-worker`, y `jupyter-lab`:

```yaml
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

### 3. Reiniciar Servicios

```bash
docker-compose down
docker-compose up -d
```

### 4. Re-ejecutar Notebooks

Ejecutar los mismos notebooks y capturar métricas nuevamente para comparar.

## Comparación de Rendimiento

### Tabla de Métricas Sugerida

| Métrica | GPU (Arch 1) | CPU (Arch 2) | Speedup |
|---------|--------------|--------------|---------|
| Input Rate (events/sec) | | | |
| Process Rate (events/sec) | | | |
| Batch Duration (ms) | | | |
| Job Time (s) | | | |
| Shuffle Read (MB) | | | |
| GC Time (s) | | | |
| Training Time (s) | | | |

## Troubleshooting

### GPU no detectada

```bash
# Verificar driver NVIDIA
nvidia-smi

# Verificar nvidia-docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Reinstalar NVIDIA Container Toolkit
# Ubuntu/Debian:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Kafka no recibe eventos

```bash
# Verificar logs del productor
docker-compose logs producer

# Verificar Kafka
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic statsbomb-360-events \
  --from-beginning --max-messages 10
```

### Spark Worker no se conecta

```bash
# Verificar logs
docker-compose logs spark-worker

# Verificar conectividad
docker exec -it spark-worker ping spark-master
```

### Jupyter Lab no carga notebooks

```bash
# Verificar permisos
sudo chown -R $(id -u):$(id -g) notebooks/

# Reiniciar servicio
docker-compose restart jupyter-lab
```

## Comandos Útiles

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f spark-master

# Reiniciar un servicio
docker-compose restart jupyter-lab

# Detener todo
docker-compose down

# Limpiar volúmenes (CUIDADO: borra datos)
docker-compose down -v

# Reconstruir imágenes
docker-compose build --no-cache

# Escalar workers (múltiples workers)
docker-compose up -d --scale spark-worker=2
```

## Recursos Adicionales

- **RAPIDS AI:** https://rapids.ai/
- **Spark Structured Streaming:** https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html
- **StatsBomb Open Data:** https://github.com/statsbomb/open-data
- **Kafka Documentation:** https://kafka.apache.org/documentation/

## Créditos

**Proyecto:** Procesamiento de Datos en Tiempo Real con Spark y GPU
**Curso:** Arquitectura de Datos - ITAM
**Dataset:** StatsBomb (Liga MX 360 Data)
**Stack:** Apache Spark, NVIDIA RAPIDS, Kafka, Docker

---

## Licencia

Este proyecto es para fines educativos. Los datos de StatsBomb están sujetos a sus propios términos de uso.
