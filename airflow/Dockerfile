FROM apache/airflow:2.10.5-python3.11

# scripts/download_dataset.sh necesita curl, zstd y tar para bajar y extraer el dump.
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl zstd tar \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Se instala junto con la misma versión de Airflow y sus constraints para que pip no
# actualice dependencias del propio Airflow. pydantic lo pide el loader de Mongo
# (valida cada documento con databases/mongodb/app/models.py).
COPY requirements.txt /tmp/requirements-pipeline.txt
RUN pip install --no-cache-dir \
    "apache-airflow==${AIRFLOW_VERSION}" \
    -r /tmp/requirements-pipeline.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.11.txt"
