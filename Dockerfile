FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code \
    && useradd -m -u 1000 spark \
    && mkdir -p /data && chown spark:spark /data

COPY pyproject.toml .
COPY main.py bot.py context.py result.py ./
COPY commands/ commands/
COPY app/ app/

RUN pip install --no-cache-dir . \
    && chown -R spark:spark /app

USER spark

ENV SPARK_DATA_DIR=/data

VOLUME ["/data"]

CMD ["python", "main.py"]
