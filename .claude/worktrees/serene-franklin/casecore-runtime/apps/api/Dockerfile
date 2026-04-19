# ============================================================
# CASECORE INTAKE_ENGINE — Production Docker Image
# ============================================================
# Build:  docker build -t casecore-api .
# Run:    docker run -p 8000:8000 --env-file .env casecore-api
# ============================================================

FROM python:3.12-slim

WORKDIR /app

# System deps for document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Copy canonical legal authority store into the image
# (In production, this could be a mounted volume or S3 bucket instead)
COPY ../../legal/canonical /app/legal/canonical

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "launch_intake.py"]
