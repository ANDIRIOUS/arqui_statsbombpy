FROM rapidsai/rapids-spark:3.3.1-cuda11-runtime-ubuntu20.04

# Set working directory
WORKDIR /work

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for StatsBomb, Kafka, and ML
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Jupyter Lab extensions (optional)
RUN pip install jupyterlab-git jupyterlab-lsp

# Create directories
RUN mkdir -p /work/notebooks /work/data /work/models

# Set environment variables
ENV JUPYTER_ENABLE_LAB=yes
ENV PYTHONUNBUFFERED=1

# Expose Jupyter Lab port
EXPOSE 8888

# Default command (will be overridden by docker-compose)
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
