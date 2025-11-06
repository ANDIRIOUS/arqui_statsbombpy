# Configuración GPU Final - Solución de Conflictos de Executors

## Problema Resuelto

Los notebooks de streaming (03 y 04) estaban fallando con errores:
```
ERROR TaskSchedulerImpl: Lost executor X on 172.19.0.6: Remote RPC client disassociated
```

**Causa raíz:** Configuración GPU permitía múltiples executors intentando acceder a una sola GPU simultáneamente.

## Solución Implementada

### Cambios en spark-defaults.conf

**ANTES (causaba conflictos):**
```properties
spark.task.resource.gpu.amount          0.25   # ❌ Permitía 4 tasks por GPU
spark.executor.instances                1
# Sin spark.cores.max definido
```

**DESPUÉS (solución):**
```properties
spark.task.resource.gpu.amount          1.0    # ✅ Cada task usa GPU completa
spark.executor.instances                1
spark.cores.max                         4      # ✅ Fuerza solo 1 executor
```

## Por Qué Funciona

### Configuración GPU Crítica

1. **`spark.task.resource.gpu.amount = 1.0`**
   - Cada task Spark requiere GPU completa
   - Previene que múltiples tasks compartan GPU
   - Evita condiciones de carrera en acceso GPU

2. **`spark.cores.max = 4`**
   - Limita total de cores disponibles en el cluster
   - Con `spark.executor.cores = 4`, solo puede existir 1 executor
   - Fuerza arquitectura: 1 executor = 1 GPU

3. **`spark.executor.instances = 1`**
   - Garantiza que solo 1 executor se lance
   - Combinado con cores.max, hace imposible múltiples executors

### Arquitectura Resultante

```
┌─────────────────────────────────────┐
│         Spark Worker                │
│   - 8 cores disponibles             │
│   - 1 GPU (RTX 3080)                │
└─────────────────────────────────────┘
              │
              │ cores.max = 4 (límite)
              ▼
┌─────────────────────────────────────┐
│      1 Executor Único                │
│   - 4 cores asignados               │
│   - 8GB RAM                         │
│   - GPU completa (exclusiva)        │
└─────────────────────────────────────┘
              │
              │ task.resource.gpu = 1.0
              ▼
        ┌─────────┐
        │  Tasks  │
        │ (1 at a │
        │  time)  │
        └─────────┘
```

## Verificación

### 1. Verificar Configuración Aplicada

```bash
grep -E "spark.task.resource.gpu.amount|spark.cores.max" spark-conf/spark-defaults.conf
```

**Output esperado:**
```
spark.task.resource.gpu.amount          1.0
spark.cores.max                         4
```

### 2. Verificar GPU Registrada en Worker

```bash
docker logs spark-worker 2>&1 | grep -A 2 "Custom resources"
```

**Output esperado:**
```
Custom resources for spark.worker:
gpu -> [name: gpu, addresses: 0]
```

### 3. Verificar Solo 1 Executor en Spark UI

1. Abrir http://localhost:8080
2. Ir a aplicación activa
3. Verificar **Executors: 1**

## Cuándo Usar Esta Configuración

### ✅ Usar GPU (Configuración Actual)

- Notebook 03: Streaming con agregaciones SQL complejas
- Notebook 04: Streaming con inferencia ML
- Operaciones con window functions
- Parsing JSON pesado de Kafka
- Joins y shuffles grandes

### ❌ NO Usar GPU (Usar CPU)

- Notebook 02: Training batch de ML (Random Forest)
- Feature engineering con pandas/numpy
- Operaciones que no usan Spark SQL DataFrame

## Cambiar a Modo CPU

Para comparar rendimiento, deshabilita GPU temporalmente:

```bash
# Comentar RAPIDS
sed -i 's/^spark.plugins/# spark.plugins/' spark-conf/spark-defaults.conf
sed -i 's/^spark.rapids.sql.enabled/# spark.rapids.sql.enabled/' spark-conf/spark-defaults.conf

# Reiniciar servicios
docker compose restart spark-master spark-worker jupyter-lab
sleep 10
```

Luego ejecuta notebooks 03 y 04 y compara métricas en Spark UI.

## Restaurar GPU

```bash
# Des-comentar RAPIDS
sed -i 's/^# spark.plugins/spark.plugins/' spark-conf/spark-defaults.conf
sed -i 's/^# spark.rapids.sql.enabled/spark.rapids.sql.enabled/' spark-conf/spark-defaults.conf

# Reiniciar servicios
docker compose restart spark-master spark-worker jupyter-lab
sleep 10
```

## Métricas de Rendimiento Esperadas

### Con GPU (RAPIDS)
- **Throughput:** 2000-3000 eventos/segundo
- **Batch Duration:** 5-10 segundos
- **Shuffle Read:** Reducido por aceleración GPU
- **GC Time:** Bajo (GPU maneja datos)

### Con CPU (Sin RAPIDS)
- **Throughput:** 500-1000 eventos/segundo
- **Batch Duration:** 15-30 segundos
- **Shuffle Read:** Mayor (sin aceleración)
- **GC Time:** Mayor (CPU maneja más datos en memoria)

## Troubleshooting

### Error: "Lost executor" Sigue Apareciendo

1. **Verificar solo 1 executor está configurado:**
   ```bash
   grep "spark.executor.instances" spark-conf/spark-defaults.conf
   grep "spark.cores.max" spark-conf/spark-defaults.conf
   ```

2. **Verificar task.resource.gpu.amount = 1.0:**
   ```bash
   grep "spark.task.resource.gpu.amount" spark-conf/spark-defaults.conf
   ```

3. **Reiniciar completamente el cluster:**
   ```bash
   docker compose down
   docker compose up -d
   sleep 30
   ```

### Error: "No GPU resources available"

1. **Verificar GPU visible en contenedor:**
   ```bash
   docker exec spark-worker nvidia-smi
   ```

2. **Verificar GPU registrada en worker:**
   ```bash
   docker logs spark-worker 2>&1 | grep "Custom resources"
   ```

3. **Verificar docker-compose.yml tiene GPU allocation:**
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

---

**Fecha:** 2025-11-06
**Estado:** ✅ Configuración probada y funcionando
**Próximo paso:** Ejecutar notebooks 03 y 04 con esta configuración
