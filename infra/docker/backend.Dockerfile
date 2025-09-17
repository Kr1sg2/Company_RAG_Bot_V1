# LexaAI Backend Dockerfile
# Builds a runtime image for the FastAPI backend and exposes port 8600

FROM python:3.12-slim AS base

# Prevents Python from writing .pyc files and enables unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# System packages required by OCR/PDF tools and some optional deps:
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
     poppler-utils \
     tesseract-ocr \
     ghostscript \
     libglib2.0-0 \
     libgl1 \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (leverages Docker layer caching)
COPY backend/requirements.txt ./
RUN pip install --upgrade --no-cache-dir pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Expose the FastAPI port
EXPOSE 8600

# Start the API with uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8600", "--workers", "2", "--proxy-headers"]
