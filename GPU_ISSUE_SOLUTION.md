# Problema con Executors Fallando - Solución

## Problema Actual

Los executors están fallando repetidamente con "Command exited with code 1". Esto está pasando porque:

1. **RAPIDS intenta inicializar GPU en cada executor**
2. **Cada executor necesita acceso exclusivo a la GPU**
3. **Solo hay 1 GPU disponible**
4. **Múltiples executors intentan acceder simultáneamente → fallo**

## Por Qué Pasa Esto

El notebook de entrenamiento (`02_Entrenamiento_Modelo_LWP.ipynb`) hace:
- Carga de datos de pandas → Spark DataFrame (operación CPU)
- Feature engineering con pandas (operación CPU)
- Entrenamiento de Random Forest con Spark ML (puede usar CPU)

**No requiere GPU** para la mayoría de las operaciones.

## Soluciones

### Opción 1: Deshabilitar RAPIDS Temporalmente (Recomendado para Training)

Para el notebook de entrenamiento, es mejor usar CPU ya que:
- Random Forest de Spark ML funciona bien en CPU
- No hay operaciones SQL complejas que se beneficien de GPU
- Evita conflictos de acceso a GPU

**Pasos:**

1. **Editar spark-conf/spark-defaults.conf:**
   ```bash
   # Comentar estas líneas:
   # spark.plugins                           com.nvidia.spark.SQLPlugin
   # spark.rapids.sql.enabled                true
   ```

2. **Reiniciar servicios:**
   ```bash
   docker compose restart spark-master spark-worker
   docker compose restart jupyter-lab
   ```

3. **Re-ejecutar notebook desde Cell 1**

### Opción 2: Configurar GPU para Uso Compartido (Complejo)

Si realmente quieres usar GPU en el training:

1. **Modificar spark-defaults.conf:**
   ```properties
   # Permitir que múltiples tasks compartan la GPU
   spark.task.resource.gpu.amount          1.0  # Cambiar de 0.25 a 1.0
   spark.executor.instances                1    # Asegurar solo 1 executor
   ```

2. **Problemas potenciales:**
   - Spark ML Random Forest NO usa GPU automáticamente
   - Solo operaciones SQL DataFrame se aceleran con RAPIDS
   - Overhead de RAPIDS puede hacer el training MÁS LENTO

### Opción 3: Usar GPU Solo para Streaming (Recomendado)

**Para Training (Notebook 02):** Usar CPU
**Para Streaming (Notebooks 03 y 04):** Usar GPU

#### Configuración Dual:

Crear dos archivos de configuración:

**spark-conf/spark-defaults-cpu.conf** (para training):
```properties
spark.plugins                           # DESHABILITADO
spark.rapids.sql.enabled                false
spark.executor.memory                   8g
spark.executor.cores                    4
spark.executor.instances                1
```

**spark-conf/spark-defaults-gpu.conf** (para streaming):
```properties
spark.plugins                           com.nvidia.spark.SQLPlugin
spark.rapids.sql.enabled                true
spark.executor.memory                   6g  # Menos memoria para dejar espacio a GPU
spark.executor.cores                    4
spark.executor.instances                1
spark.task.resource.gpu.amount          1.0  # GPU completa por task
```

Luego copiar el apropiado antes de ejecutar cada notebook.

## Recomendación Final

**Para continuar AHORA:**

1. **Deshabilitar RAPIDS temporalmente** (Opción 1)
2. **Completar el training del modelo** (notebook 02)
3. **Re-habilitar RAPIDS** antes de ejecutar los notebooks de streaming (03 y 04)

Los notebooks de streaming SÍ se benefician de GPU porque:
- Procesan Kafka streams con operaciones SQL
- Hacen aggregaciones complejas en ventanas de tiempo
- RAPIDS acelera estas operaciones significativamente

Pero el training batch con Random Forest de Spark ML no usa GPU de todas formas.

## Comando Rápido para Deshabilitar RAPIDS

```bash
cd /home/schafler/ITAM/arqui/final2

# Backup de configuración actual
cp spark-conf/spark-defaults.conf spark-conf/spark-defaults-gpu-backup.conf

# Comentar las líneas de RAPIDS
sed -i 's/^spark.plugins/# spark.plugins/' spark-conf/spark-defaults.conf
sed -i 's/^spark.rapids.sql.enabled/# spark.rapids.sql.enabled/' spark-conf/spark-defaults.conf
sed -i 's/^spark.rapids.sql.explain/# spark.rapids.sql.explain/' spark-conf/spark-defaults.conf
sed -i 's/^spark.rapids.memory.pinnedPool.size/# spark.rapids.memory.pinnedPool.size/' spark-conf/spark-defaults.conf

# Reiniciar servicios
docker compose restart spark-master spark-worker jupyter-lab
```

## Para Re-habilitar GPU Después

```bash
# Restaurar configuración con GPU
cp spark-conf/spark-defaults-gpu-backup.conf spark-conf/spark-defaults.conf

# Reiniciar servicios
docker compose restart spark-master spark-worker jupyter-lab
```
