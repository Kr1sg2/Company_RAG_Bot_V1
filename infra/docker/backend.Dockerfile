# LexaAI Backend Dockerfile
# Builds a runtime image for the FastAPI backend and exposes port 8600

FROM python:3.12-slim AS base

# Prevents Python from writing .pyc files and enables unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Install build essentials only if a package needs compilation (kept minimal)
# Note: Most deps have prebuilt wheels; OS tools like poppler/tesseract are not
# required for image build and can be added at deploy-time if runtime OCR is needed.

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
