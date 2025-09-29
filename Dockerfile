FROM python:3.11-slim

WORKDIR /app

# Install OS deps for asyncpg and image processing (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app


# Install Python deps
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# make entrypoint executable
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "run.py"]
