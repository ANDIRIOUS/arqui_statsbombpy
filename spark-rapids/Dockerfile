# Custom Spark 3.3.1 + RAPIDS Accelerator Image
# Base: NVIDIA CUDA 11.8 Runtime on Ubuntu 22.04

FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    python3.10 \
    python3-pip \
    wget \
    curl \
    procps \
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
# Using version 23.12.2 which is compatible with Spark 3.3.1 and CUDA 11.8
ENV RAPIDS_VERSION=23.12.2
ENV SCALA_VERSION=2.12

RUN mkdir -p ${SPARK_HOME}/jars && \
    wget -q -P ${SPARK_HOME}/jars \
    https://repo1.maven.org/maven2/com/nvidia/rapids-4-spark_${SCALA_VERSION}/${RAPIDS_VERSION}/rapids-4-spark_${SCALA_VERSION}-${RAPIDS_VERSION}.jar

# Download additional RAPIDS dependencies (cuDF for CUDA 11)
# Note: Using 23.12.1 as 23.12.0 was not published to Maven Central
RUN wget -P ${SPARK_HOME}/jars \
    https://repo1.maven.org/maven2/ai/rapids/cudf/23.12.1/cudf-23.12.1-cuda11.jar

# Install Python packages for Spark
RUN pip3 install --no-cache-dir \
    pyspark==${SPARK_VERSION} \
    py4j==0.10.9.5

# Create GPU discovery script for Spark
RUN echo '#!/bin/bash\n\
echo {\n\
echo \\"name\\": \\"gpu\\",\n\
echo \\"addresses\\": [\n\
nvidia-smi --query-gpu=index --format=csv,noheader | awk '"'"'{print "\\"" $1 "\\""}'"'"' | paste -sd "," -\n\
echo ]\n\
echo }\n' > ${SPARK_HOME}/getGpusResources.sh && \
    chmod +x ${SPARK_HOME}/getGpusResources.sh

# Set Spark environment variables
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# Create directories
RUN mkdir -p /opt/spark/work-dir /opt/spark/logs /tmp/spark-events /tmp/spark-checkpoints && \
    chmod 777 /tmp/spark-events /tmp/spark-checkpoints

# Set working directory
WORKDIR ${SPARK_HOME}

# Expose Spark ports
EXPOSE 8080 7077 6066 4040 4041

# Default command
CMD ["/bin/bash"]
