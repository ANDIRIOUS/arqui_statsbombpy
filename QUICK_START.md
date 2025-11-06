# Quick Start Guide - Spark GPU Streaming Project

## ✅ System is Running!

All services are successfully deployed and operational.

## Current Status

### Services Running
- ✅ **Zookeeper** - Port 2181
- ✅ **Kafka** - Ports 9092 (internal), 9093 (external)
- ✅ **Producer** - Streaming **~3000+ events/sec** to Kafka
- ✅ **Spark Master** - Port 8080 (UI), 7077 (cluster)
- ✅ **Spark Worker** - Port 8081 (UI)
- ✅ **Jupyter Lab** - Port 8888

### GPU Configuration
- **GPU Detected:** NVIDIA GeForce RTX 3080 Laptop GPU (8GB VRAM)
- **Driver Version:** 580.95.05
- **CUDA Version:** 11.8
- **RAPIDS JARs Installed:**
  - rapids-4-spark_2.12-23.12.2.jar (536MB)
  - cudf-23.12.1-cuda11.jar (445MB)

### Producer Status
- ✅ Streaming events to Kafka
- 📊 **Throughput:** ~3059 events/second
- 🔄 Infinite loop replay of StatsBomb 360 data
- 📝 Topic: `statsbomb-360-events`

## Access Points

### 1. Jupyter Lab (Development Environment)
```
http://localhost:8888
```
- **No token required** (disabled for development)
- Navigate to `/work/notebooks/` to see the 3 notebooks

### 2. Spark Master UI
```
http://localhost:8080
```
- View cluster status
- Check worker connections
- Monitor running applications

### 3. Spark Worker UI
```
http://localhost:8081
```
- View worker resources
- Check executor status

### 4. Spark Application UI (when running jobs)
```
http://localhost:4040
```
- **Only available when Spark job is running**
- View streaming metrics
- Capture performance data for GPU vs CPU comparison

## Next Steps

### Step 1: Train the ML Model (LWP)

Open Jupyter Lab and run:
```
notebooks/02_Entrenamiento_Modelo_LWP.ipynb
```

**What it does:**
- Loads 4 seasons of La Liga data from StatsBomb (2017-2021)
- Performs feature engineering with 360 data
- Trains Random Forest classifier for Live Win Probability
- Saves model to `/work/models/lwp_model`

**Expected time:** 15-30 minutes (depends on API rate limits)

**Note:** Notebook uses La Liga (competition_id=11) instead of Liga MX as it has more data available in StatsBomb open data. See [NOTEBOOK_FIX.md](NOTEBOOK_FIX.md) for details.

### Step 2: Run Real-Time Statistics

Run:
```
notebooks/03_Streaming_Estadisticas.ipynb
```

**What it does:**
- Consumes Kafka stream (3000+ events/sec)
- Calculates statistics in 1-minute windows
- Computes min, max, avg, variance for passes, positions, shots
- Outputs results to console

**Metrics to capture from Spark UI (http://localhost:4040):**
- Input Rate (events/second)
- Process Rate (events/second)
- Batch Duration
- Scheduling Delay
- Shuffle Read/Write
- GC Time

### Step 3: Run ML Inference on Stream

Run:
```
notebooks/04_Streaming_Inferencia_LWP.ipynb
```

**What it does:**
- Loads trained LWP model
- Applies model to live Kafka stream
- Predicts win probabilities in real-time
- Outputs: P(Home Win), P(Draw), P(Away Win)

**Additional metrics to capture:**
- ML inference overhead (batch duration increase)
- Memory usage with model loaded
- GPU utilization during inference

## Comparing GPU vs CPU Performance

### To Switch to CPU (Architecture 2):

1. **Stop services:**
   ```bash
   docker compose down
   ```

2. **Disable RAPIDS in `spark-conf/spark-defaults.conf`:**
   ```bash
   # Comment out these lines:
   # spark.plugins                           com.nvidia.spark.SQLPlugin
   # spark.rapids.sql.enabled                true
   # spark.rapids.sql.explain                ALL
   # spark.rapids.memory.pinnedPool.size     2G
   ```

3. **Remove GPU allocation in `docker-compose.yml`:**
   Comment out `deploy.resources.reservations.devices` sections for:
   - spark-master
   - spark-worker
   - jupyter-lab

4. **Restart:**
   ```bash
   docker compose up -d
   ```

5. **Re-run notebooks 03 and 04** and capture metrics again

### Metrics Comparison Table

| Metric | GPU (Current) | CPU (After Switch) |
|--------|---------------|---------------------|
| Input Rate | | |
| Process Rate | | |
| Batch Duration | | |
| Job Time | | |
| Shuffle Read | | |
| GC Time | | |

## Troubleshooting

### Check service status
```bash
docker compose ps
```

### View logs for specific service
```bash
docker compose logs -f producer      # Producer
docker compose logs -f spark-master  # Spark Master
docker compose logs -f jupyter-lab   # Jupyter Lab
```

### Restart a service
```bash
docker compose restart producer
```

### Stop all services
```bash
docker compose down
```

### Restart everything
```bash
docker compose down
docker compose up -d
```

### Verify GPU access
```bash
docker exec spark-master nvidia-smi
```

### Check RAPIDS JARs
```bash
docker exec spark-master ls -lh /opt/spark/jars/ | grep -E "rapids|cudf"
```

### Check producer throughput
```bash
docker compose logs producer --tail 5
```

## Useful Commands

```bash
# View all container resource usage
docker stats

# Execute command in Spark master
docker exec -it spark-master bash

# Check Kafka topics
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Consume from Kafka (test)
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic statsbomb-360-events \
  --max-messages 5

# Rebuild specific service
docker compose build producer
docker compose up -d producer
```

## Project Structure

```
/work/notebooks/          # Jupyter notebooks (in container)
  ├── 02_Entrenamiento_Modelo_LWP.ipynb
  ├── 03_Streaming_Estadisticas.ipynb
  └── 04_Streaming_Inferencia_LWP.ipynb

/work/data/              # Data storage (persistent)
/work/models/            # Trained models (persistent)
/opt/spark/conf/         # Spark configuration
```

## Performance Notes

### Current Configuration
- **GPU:** RTX 3080 Laptop (8GB VRAM)
- **RAPIDS:** Enabled
- **Streaming Rate:** ~3000 events/sec (producer)
- **Target Rate:** 4096 events/sec (can be increased in producer)

### Expected Speedups (GPU vs CPU)
- DataFrame operations: 3-10x faster
- ML training: 5-20x faster (depends on model)
- Aggregations: 2-5x faster

## Important Files

- `docker-compose.yml` - Service orchestration
- `spark-conf/spark-defaults.conf` - Spark GPU/CPU configuration
- `producer/producer.py` - Kafka event simulator
- `.env` - StatsBomb credentials (not tracked in git)

## Getting Help

- **Spark Documentation:** https://spark.apache.org/docs/3.3.1/
- **RAPIDS Accelerator:** https://nvidia.github.io/spark-rapids/
- **StatsBomb API:** https://github.com/statsbomb/statsbombpy
- **Project Issues:** Check logs with `docker compose logs <service>`

---

**Status as of:** 2025-11-05
**All systems operational** ✅
