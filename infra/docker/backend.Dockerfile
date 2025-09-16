FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory (this should be backend directory)
WORKDIR /app/backend

# Copy backend directory
COPY backend/ /app/backend/
COPY pyproject.toml* requirements*.txt* /app/

# Install Python dependencies with best-effort detection
RUN if [ -f /app/backend/requirements.txt ]; then \
        pip install -r /app/backend/requirements.txt; \
    elif [ -f /app/requirements.txt ]; then \
        pip install -r /app/requirements.txt; \
    elif [ -f /app/pyproject.toml ]; then \
        pip install .; \
    fi

# Expose port
EXPOSE 8601

# Default command
CMD ["python", "-m", "uvicorn", "lexa_app.main:app", "--host", "0.0.0.0", "--port", "8601"]