FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1000 spark \
    && mkdir -p /data && chown spark:spark /data

COPY requirements.txt .
COPY app/ app/

RUN pip install --no-cache-dir -r requirements.txt \
    && chown -R spark:spark /app

USER spark

ENV SPARK_DATA_DIR=/data

VOLUME ["/data"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
