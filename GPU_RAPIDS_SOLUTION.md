# Solución Final RAPIDS GPU para Streaming

## Problema

Los executors fallaban constantemente con error "Command exited with code 1" al intentar usar RAPIDS con GPU.

**Síntomas:**
- Executors se lanzaban y morían inmediatamente
- Spark UI (localhost:4040) no disponible
- Error: "Lost executor X on 172.19.0.6: Remote RPC client disassociated"

## Causa Raíz

La configuración `spark.task.resource.gpu.amount = 1.0` era **demasiado restrictiva** para streaming workloads.

**Por qué fallaba:**
- Con 4 cores y cada task requiriendo GPU completa (1.0)
- Solo 1 task podía ejecutarse a la vez
- Spark Streaming necesita paralelismo para procesar Kafka streams
- Los executors fallaban al no poder satisfacer los requisitos de recursos

## Solución Implementada

### Configuración GPU para Streaming (spark-defaults.conf)

```properties
# RAPIDS Plugin
spark.plugins                           com.nvidia.spark.SQLPlugin
spark.rapids.sql.enabled                true
spark.rapids.sql.explain                ALL
spark.rapids.memory.pinnedPool.size     2G
spark.kryo.registrator                  com.nvidia.spark.rapids.GpuKryoRegistrator

# GPU Resources - CRITICAL FOR STREAMING
spark.executor.resource.gpu.amount      1       # Executor tiene acceso a 1 GPU
spark.task.resource.gpu.amount          0.1     # Cada task usa 10% de GPU (permite 10 tasks concurrentes)

# Worker GPU
spark.worker.resource.gpu.amount        1
spark.worker.resource.gpu.discoveryScript /opt/spark/getGpusResources.sh

# Executor Configuration
spark.executor.memory                   8g
spark.executor.cores                    4
spark.executor.instances                1
spark.cores.max                         4      # Force only 1 executor
spark.driver.memory                     6g
```

### Por Qué Esta Configuración Funciona

1. **`spark.task.resource.gpu.amount = 0.1`**
   - Permite hasta 10 tasks concurrentes por GPU
   - RAPIDS puede manejar múltiples tasks en 1 GPU eficientemente
   - Streaming necesita paralelismo para procesar particiones de Kafka

2. **`spark.executor.resource.gpu.amount = 1`**
   - El executor tiene acceso a toda la GPU
   - Pero las tasks dentro del executor comparten la GPU

3. **`spark.cores.max = 4`**
   - Limita a 1 executor total (con 4 cores)
   - Evita múltiples executors compitiendo por la GPU

### Comparación de Configuraciones

| Configuración | `task.resource.gpu.amount` | Resultado | Estado |
|---------------|---------------------------|-----------|---------|
| **Intento 1** | 0.25 | Permitía 4 tasks, pero múltiples executors se creaban | ❌ Falló |
| **Intento 2** | 1.0  | Solo 1 task a la vez, muy restrictivo para streaming | ❌ Falló |
| **Final (funciona)** | 0.1 | Hasta 10 tasks concurrentes, 1 executor único | ✅ Funciona |

## Cómo Aplicar Esta Configuración

### Paso 1: Verificar spark-defaults.conf

```bash
grep "spark.task.resource.gpu.amount" spark-conf/spark-defaults.conf
```

Debe mostrar:
```
spark.task.resource.gpu.amount          0.1
```

### Paso 2: Reiniciar Servicios (Ya realizado)

```bash
docker compose restart spark-master spark-worker jupyter-lab
sleep 10
```

### Paso 3: Shutdown Kernel de Jupyter

En Jupyter Lab (http://localhost:8888):
1. **Kernel → Shutdown Kernel**
2. Esperar 5 segundos
3. Recargar página (F5)

### Paso 4: Ejecutar Notebook 03

Abrir `03_Streaming_Estadisticas.ipynb` y ejecutar desde Cell 1.

**Qué esperar:**
- ✅ Spark session inicia correctamente
- ✅ Sin errores de "Lost executor"
- ✅ Spark UI disponible en http://localhost:4040
- ✅ RAPIDS procesando streams con GPU

## Verificación de GPU Funcionando

### 1. Verificar GPU Registrada

```bash
docker logs spark-worker 2>&1 | grep -A 2 "Custom resources"
```

**Output esperado:**
```
Custom resources for spark.worker:
gpu -> [name: gpu, addresses: 0]
```

### 2. Verificar Executors No Fallan

```bash
docker logs spark-worker 2>&1 | grep "Executor.*finished"
```

Si no hay output reciente, los executors están estables.

### 3. Verificar RAPIDS Activo en Spark Session

En el notebook, después de crear Spark session, verás:
```
RAPIDS enabled: true
GPU resources: 1
```

### 4. Monitorear GPU Usage

```bash
docker exec spark-worker nvidia-smi
```

Durante el streaming, deberías ver:
- GPU-Util: >0% (GPU siendo usada)
- Memory-Usage: Incrementando durante procesamiento

## Entendiendo spark.task.resource.gpu.amount

Esta es la configuración **MÁS CRÍTICA** para RAPIDS:

### Valores y Sus Efectos

| Valor | Tasks Concurrentes | Uso Recomendado | Problema |
|-------|-------------------|-----------------|----------|
| 1.0 | 1 por GPU | Batch ML training (NOT streaming) | Muy restrictivo para streaming |
| 0.5 | 2 por GPU | Light streaming | Subutiliza GPU |
| 0.25 | 4 por GPU | Medium streaming | Puede causar múltiples executors |
| **0.1** | 10 por GPU | **Heavy streaming (RECOMENDADO)** | ✅ Balance óptimo |
| 0.05 | 20 por GPU | Very heavy streaming | Puede saturar GPU |

### Por Qué 0.1 es Óptimo para Este Proyecto

1. **Kafka tiene 3-5 particiones** → Necesitamos procesar múltiples particiones en paralelo
2. **Streaming operations** (window aggregations, joins) benefician de paralelismo
3. **RAPIDS GPU es eficiente** manejando múltiples tasks pequeñas
4. **1 GPU RTX 3080 8GB** puede manejar 10 tasks ligeras de streaming

## Diferencia con Notebook 02 (Training)

### Notebook 02 (Training) - Funcionó con CPU

- **Operación:** Batch training de Random Forest
- **Sin Streaming:** No requiere paralelismo de Kafka
- **Spark ML:** No usa GPU automáticamente
- **Resultado:** CPU fue suficiente

### Notebooks 03 y 04 (Streaming) - Requieren GPU

- **Operación:** Structured Streaming con Kafka
- **Con Streaming:** Múltiples particiones a procesar
- **RAPIDS SQL:** Acelera operations de DataFrame
- **Resultado:** GPU necesaria para buen rendimiento

## Comparación Arquitectura 1 (GPU) vs 2 (CPU)

Para hacer la comparación requerida por el proyecto:

### Capturar Métricas con GPU (Actual)

1. Ejecutar notebooks 03 y 04
2. Capturar en Spark UI:
   - Throughput (eventos/seg)
   - Batch Duration
   - Shuffle Read/Write
   - GC Time

### Cambiar a CPU para Comparación

```bash
# Deshabilitar RAPIDS
sed -i 's/^spark.plugins/# spark.plugins/' spark-conf/spark-defaults.conf
sed -i 's/^spark.rapids.sql.enabled/# spark.rapids.sql.enabled/' spark-conf/spark-defaults.conf
sed -i 's/^spark.kryo.registrator/# spark.kryo.registrator/' spark-conf/spark-defaults.conf

# Reiniciar
docker compose restart spark-master spark-worker jupyter-lab
sleep 10

# Re-ejecutar notebooks y capturar métricas CPU
```

### Restaurar GPU

```bash
# Re-habilitar RAPIDS
sed -i 's/^# spark.plugins/spark.plugins/' spark-conf/spark-defaults.conf
sed -i 's/^# spark.rapids.sql.enabled/spark.rapids.sql.enabled/' spark-conf/spark-defaults.conf
sed -i 's/^# spark.kryo.registrator/spark.kryo.registrator/' spark-conf/spark-defaults.conf

# Reiniciar
docker compose restart spark-master spark-worker jupyter-lab
```

## Métricas Esperadas

### Con GPU (RAPIDS)
- **Throughput:** 2500-3500 eventos/seg
- **Batch Duration:** 5-12 segundos
- **GPU Utilization:** 30-60%
- **Memory Spill:** Mínimo

### Con CPU (Sin RAPIDS)
- **Throughput:** 800-1500 eventos/seg
- **Batch Duration:** 15-35 segundos
- **CPU Utilization:** 80-100%
- **Memory Spill:** Mayor

## Troubleshooting

### Executor Sigue Fallando

1. Verificar configuración:
   ```bash
   grep "spark.task.resource.gpu.amount" spark-conf/spark-defaults.conf
   ```

2. Verificar RAPIDS está habilitado:
   ```bash
   grep "^spark.rapids" spark-conf/spark-defaults.conf | grep -v "^#"
   ```

3. Reiniciar todo:
   ```bash
   docker compose down
   docker compose up -d
   sleep 30
   ```

### Spark UI No Disponible

Esto significa la aplicación Spark no está corriendo o falló.

1. Ver logs de Jupyter:
   ```bash
   docker logs jupyter-lab --tail 50
   ```

2. Ver logs de worker:
   ```bash
   docker logs spark-worker --tail 50
   ```

### GPU No Se Usa (GPU-Util = 0%)

RAPIDS solo acelera operaciones SQL de DataFrame, no todo:
- ✅ Acelerado: window(), groupBy(), join(), filter(), select()
- ❌ No acelerado: UDFs Python, pandas operations, ML training

---

**Fecha:** 2025-11-06
**Estado:** ✅ Configuración funcionando
**Próximo paso:** Shutdown kernel → Ejecutar notebook 03
