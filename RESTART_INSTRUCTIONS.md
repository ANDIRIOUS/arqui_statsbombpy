# Instrucciones para Reiniciar con Nueva Configuración

## Problema Actual

Tu sesión de Spark actual está en estado **WAITING** porque:
- Se inició con la configuración antigua (12GB por executor, 2 executors)
- El worker solo tiene 16GB disponibles
- No puede asignar los recursos solicitados

## Solución: Reiniciar Sesión de Spark

### Opción 1: Desde Jupyter Lab (Recomendado)

1. **Detener el kernel actual:**
   - En Jupyter Lab, ve al menu: `Kernel` → `Shutdown Kernel`
   - Confirma "Shutdown"

2. **Esperar 5 segundos** para que Spark libere los recursos

3. **Iniciar nuevo kernel:**
   - Click en el botón `Select Kernel` arriba a la derecha
   - Selecciona el kernel de Python 3

4. **Re-ejecutar el notebook:**
   - Ejecuta todas las celdas desde Cell 1
   - La nueva sesión usará la configuración actualizada (8GB, 1 executor)

### Opción 2: Reiniciar Contenedor Jupyter (Si Opción 1 no funciona)

```bash
# Detener y reiniciar el contenedor de Jupyter
docker compose restart jupyter-lab

# Esperar 10 segundos para que se reinicie
sleep 10

# Abrir Jupyter Lab nuevamente
# http://localhost:8888
```

Luego ejecuta el notebook desde el inicio.

### Opción 3: Reiniciar Todo el Cluster (Último recurso)

```bash
# Detener todos los servicios
docker compose down

# Reiniciar todo
docker compose up -d

# Esperar que todos los servicios estén listos
sleep 30

# Verificar que todo esté corriendo
docker compose ps
```

## Verificación de Éxito

Después de reiniciar, cuando ejecutes Cell 4 (Spark Session), deberías ver en los logs:

✅ **Sin warnings repetitivos** de "Initial job has not accepted any resources"

✅ **En Spark Master UI** (http://localhost:8080):
   - Application State: **RUNNING** (no WAITING)
   - Cores: **4 Used** (o más, dependiendo del job)
   - Memory: **8 GiB** por executor

## Nueva Configuración de Memoria

La configuración actualizada en [spark-conf/spark-defaults.conf](spark-conf/spark-defaults.conf):

```properties
spark.executor.memory                   8g      # Reducido de 12g
spark.executor.instances                1       # Reducido de 2
spark.driver.memory                     6g      # Reducido de 8g
```

**Uso total:**
- Driver: 6GB
- Executor: 8GB
- **Total: 14GB** ✅ (cabe en 16GB disponibles)

## Comandos Útiles para Monitoreo

```bash
# Ver logs de Jupyter Lab
docker logs -f jupyter-lab --tail 20

# Ver aplicaciones Spark activas
docker exec spark-master curl -s http://localhost:8080 | grep -A 5 "Running Applications"

# Ver recursos del worker
docker exec spark-master curl -s http://spark-worker:8081 | grep -E "Memory:|Cores:"

# Verificar GPU
docker exec jupyter-lab nvidia-smi
```

## Si Aún Tienes Problemas

Si después de reiniciar sigues viendo el warning "Initial job has not accepted any resources", puede ser que:

1. **El notebook está usando configuración hardcodeada:** Verifica que en Cell 4 no haya líneas como:
   ```python
   .config("spark.executor.memory", "12g")  # ← Esto sobreescribe spark-defaults.conf
   ```

2. **Caché de configuración:** El archivo `spark-defaults.conf` se monta como volumen, pero si hay caché, prueba:
   ```bash
   docker compose restart spark-master
   docker compose restart spark-worker
   ```

3. **Recursos insuficientes:** Verifica que tu sistema tenga suficiente RAM disponible:
   ```bash
   free -h
   ```

---

**Recomendación:** Usa **Opción 1** primero. Es la forma más limpia y rápida.
