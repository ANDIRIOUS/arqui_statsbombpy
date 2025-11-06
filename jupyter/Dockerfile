FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /work

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    python3.10 \
    python3-pip \
    curl \
    wget \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set Java home
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$JAVA_HOME/bin

# Download and install Apache Spark 3.3.1
ENV SPARK_VERSION=3.3.1
ENV HADOOP_VERSION=3
ENV SPARK_HOME=/opt/spark
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
    && tar -xzf spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz \
    && mv spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION} ${SPARK_HOME} \
    && rm spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz

# Download RAPIDS Accelerator for Apache Spark
ENV RAPIDS_VERSION=23.12.2
ENV SCALA_VERSION=2.12

RUN mkdir -p ${SPARK_HOME}/jars && \
    wget -P ${SPARK_HOME}/jars \
    https://repo1.maven.org/maven2/com/nvidia/rapids-4-spark_${SCALA_VERSION}/${RAPIDS_VERSION}/rapids-4-spark_${SCALA_VERSION}-${RAPIDS_VERSION}.jar && \
    wget -P ${SPARK_HOME}/jars \
    https://repo1.maven.org/maven2/ai/rapids/cudf/23.12.1/cudf-23.12.1-cuda11.jar

# Set Spark environment variables
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Install Python packages for StatsBomb, Kafka, and ML
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Install Jupyter Lab extensions (optional)
RUN pip3 install jupyterlab-git jupyterlab-lsp

# Create directories
RUN mkdir -p /work/notebooks /work/data /work/models /tmp/spark-events /tmp/spark-checkpoints

# Set environment variables
ENV JUPYTER_ENABLE_LAB=yes
ENV PYTHONUNBUFFERED=1

# Expose Jupyter Lab port
EXPOSE 8888

# Default command (will be overridden by docker-compose)
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
