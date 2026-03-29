# 🐳 Stage 1: Build & Dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies for Scapy and AI libraries
RUN apt-get update && apt-get install -y \
    gcc \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 🐳 Stage 2: Final Production Runtime
FROM python:3.11-slim

WORKDIR /app

# Runtime dependencies (must include libpcap for Scapy and curl for health checks)
RUN apt-get update && apt-get install -y \
    libpcap-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY ./app ./app
COPY ./requirements.txt .

# Create data directory for persistence
RUN mkdir -p data

# Environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV DATA_DIR=/app/data

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
