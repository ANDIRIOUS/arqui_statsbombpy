# Corrección del Notebook de Entrenamiento

## Problemas Encontrados y Corregidos

### Problema 1: Datos de Liga MX No Disponibles

El notebook `02_Entrenamiento_Modelo_LWP.ipynb` estaba configurado para usar datos de **Liga MX** (competition_id=40), pero este torneo no está disponible en los datos abiertos de StatsBomb.

**Error Original:**
```
ValueError: No objects to concatenate
```

Este error ocurría porque:
1. `liga_mx = competitions[competitions['competition_id'] == 40]` retornaba un DataFrame vacío
2. `season_ids = liga_mx['season_id'].tail(4).tolist()` creaba una lista vacía
3. `pd.concat(all_matches, ignore_index=True)` fallaba al intentar concatenar una lista vacía

### Problema 2: Incompatibilidad pandas 2.0+ con PySpark 3.3.1

**Error:**
```
AttributeError: 'DataFrame' object has no attribute 'iteritems'
```

Este error ocurría porque:
- PySpark 3.3.1 usa el método `iteritems()` internamente
- pandas 2.0+ eliminó `iteritems()` (fue deprecado en 1.5.x)
- La imagen de Jupyter tenía pandas 2.0.3 instalado

**Solución:** Downgrade a pandas 1.5.3 para compatibilidad con PySpark 3.3.1

## Solución Implementada

Se cambió la configuración para usar **La Liga** (competition_id=11), que tiene abundantes datos disponibles:

### Competiciones Disponibles en StatsBomb Open Data

Las principales competiciones con múltiples temporadas son:

| Competition ID | Nombre | Temporadas Disponibles |
|----------------|--------|------------------------|
| 11 | **La Liga** | 2004/2005 - 2020/2021 (17 temporadas) |
| 16 | Champions League | 1999/2000 - 2018/2019 (20 temporadas) |
| 9 | Bundesliga | 2015/2016, 2023/2024 |
| 43 | FIFA World Cup | 1958, 1962, 1970, 1974, 1986, 1990, 2018, 2022 |
| 2 | Premier League | 2003/2004, 2015/2016 |
| 7 | Ligue 1 | 2015/2016, 2021/2022, 2022/2023 |
| 72 | Women's World Cup | 2019, 2023 |

**La Liga fue elegida** porque:
- ✅ Es una liga española (similar contexto a Liga MX)
- ✅ Tiene 17 temporadas disponibles (la mayor cantidad)
- ✅ Incluye datos 360 de StatsBomb
- ✅ Es una liga de alto nivel con datos de calidad

### Cambios Realizados

#### 1. Notebook actualizado para usar La Liga

**Archivo:** `notebooks/02_Entrenamiento_Modelo_LWP.ipynb`

- **Cell 0 (Markdown)** - Título actualizado:
  ```markdown
  **Datos:** 4 temporadas de La Liga con datos 360 de StatsBomb
  ```

- **Cell 6 (Code)** - Competition ID cambiado:
  ```python
  # La Liga competition ID (changed from Liga MX as it's not available in open data)
  COMPETITION_ID = 11  # La Liga

  print("Cargando competiciones...")
  competitions = sb.competitions()
  la_liga = competitions[competitions['competition_id'] == COMPETITION_ID]
  print(f"\nTemporadas disponibles de La Liga:")
  print(la_liga[['season_id', 'season_name']])

  # Get the last 4 seasons
  season_ids = la_liga['season_id'].tail(4).tolist()
  print(f"\nTemporadas seleccionadas: {season_ids}")
  ```

#### 2. Pandas downgradeado para compatibilidad

**Archivo:** `jupyter/requirements.txt`

```diff
- pandas==2.0.3
+ pandas==1.5.3  # Changed from 2.0.3 for PySpark 3.3.1 compatibility (iteritems deprecated in 2.0+)
```

**Aplicado al contenedor:**
```bash
docker exec jupyter-lab pip install pandas==1.5.3
```

## Cómo Proceder

### 1. Abrir Jupyter Lab
```
http://localhost:8888
```

### 2. Re-ejecutar el Notebook

**Reiniciar el kernel** para limpiar el estado anterior:
- Menu: `Kernel` → `Restart Kernel and Clear All Outputs`

Luego ejecutar todas las celdas en orden:
- Menu: `Run` → `Run All Cells`

O ejecutar celda por celda con `Shift + Enter`

### 3. Temporadas que se Cargarán

Las últimas 4 temporadas de La Liga disponibles serán:
- 2017/2018
- 2018/2019
- 2019/2020
- 2020/2021

### 4. Tiempo Estimado

**Total:** ~15-30 minutos dependiendo de la velocidad de la API de StatsBomb

- **Celdas 1-5:** < 1 minuto (setup y Spark session)
- **Celda 6-7:** 2-5 minutos (cargar partidos de 4 temporadas)
- **Celda 10:** 15-25 minutos (extraer features de 50 partidos)
  - Cada partido requiere una llamada a la API de StatsBomb
  - ~18-30 segundos por partido
- **Celdas 11-26:** 1-3 minutos (entrenar modelo y evaluarlo)

### 5. Monitorear Progreso

Durante la ejecución de la celda 10 verás:
```
Extrayendo características de los partidos...
[1/50] Procesando match 123456... ✓ 19 snapshots
[2/50] Procesando match 123457... ✓ 18 snapshots
...
```

### 6. Resultado Esperado

Al finalizar tendrás:
- ✅ Modelo Random Forest entrenado
- ✅ Modelo guardado en `/work/models/lwp_model`
- ✅ Métricas de accuracy y F1 score
- ✅ Feature importance calculado
- ✅ Test de inferencia exitoso

## Alternativas Adicionales

Si deseas experimentar con otros torneos, puedes cambiar `COMPETITION_ID` a:

```python
# Otras opciones interesantes:
COMPETITION_ID = 16  # Champions League (muchas temporadas)
COMPETITION_ID = 43  # FIFA World Cup (varios mundiales)
COMPETITION_ID = 2   # Premier League (2 temporadas)
COMPETITION_ID = 9   # Bundesliga (2 temporadas)
```

## Notas Importantes

1. **API Rate Limiting:** StatsBomb puede tener límites de tasa. Si encuentras errores 429, espera unos minutos antes de reintentar.

2. **Sin Credenciales:** El sistema usa `statsbombpy` sin credenciales, lo cual está bien para datos abiertos. Si tuvieras acceso de pago, podrías configurar credenciales en el archivo `.env` para acceder a más competiciones.

3. **Datos 360:** No todos los partidos tienen datos 360. El código maneja esto correctamente.

4. **GPU vs CPU:** Este notebook funciona en ambos modos (GPU y CPU). Las métricas de rendimiento se capturarán en Spark UI durante la ejecución.

---

**Estado:** ✅ Corrección completada
**Próximo paso:** Re-ejecutar el notebook 02 desde el principio
