# Company RAG Bot V1

A production-ready Retrieval-Augmented Generation (RAG) chatbot for company knowledge management. Built with FastAPI backend and React frontend, using ChromaDB for vector storage and OpenAI for language generation.

## Features

- **Semantic Search**: Vector-based document retrieval with ChromaDB
- **Source Attribution**: Precise page-level citations for all answers
- **Admin Interface**: Configuration management and system monitoring
- **Production Ready**: Docker containerization with CI/CD workflows
- **Extensible**: Modular architecture for easy customization

## Quick Start

### Development Setup

#### Backend (FastAPI)

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Set up environment (copy .env.example to .env and configure)
cp .env.example .env
# Edit .env with your OpenAI API key and other settings

# Run backend
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8601
```

#### Frontend (React + Vite)

```bash
# Install dependencies
cd frontend
npm ci

# Ensure backend is running on localhost:8601
# Vite dev server will proxy /api requests to backend

# Run frontend
npm run dev
# Frontend available at http://localhost:8080
```

### Docker Development

```bash
# Build and run with Docker Compose
docker compose -f infra/docker-compose.dev.yml up --build

# Services will be available at:
# Frontend: http://localhost:8082
# Backend: http://localhost:8601
```

### Production Deployment

```bash
# Update image references in docker-compose.prod.yml
# Replace ${OWNER_REPO_LOWER} with your GitHub repo (e.g., kr1sg2/company_rag_bot_v1)

# Deploy with production configuration
docker compose -f infra/docker-compose.prod.yml up -d
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional
OPENAI_BASE_URL=https://api.openai.com/v1  # For custom endpoints
OPENAI_MODEL=gpt-4                         # Model to use
ADMIN_PASSWORD=your-secure-password        # Admin access
SECRET_KEY=your-secret-key                 # Session encryption
```

### GitHub Secrets (for CI/CD)

Set these in your GitHub repository settings:

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `OPENAI_BASE_URL` (optional): Custom OpenAI endpoint
- `OPENAI_MODEL` (optional): Preferred model (recommended)

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System design and data flow
- [Operations Guide](docs/OPERATIONS.md) - Deployment and maintenance
- [Accuracy Plan](docs/ACCURACY_PLAN.md) - Evaluation and quality assurance
- [Development Issues](docs/ISSUES_BUNDLE.md) - Starter improvement ideas

## Technology Stack

- **Backend**: Python 3.11, FastAPI, ChromaDB, OpenAI API
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS
- **Infrastructure**: Docker, GitHub Actions, GHCR
- **Deployment**: Docker Compose, Nginx (reverse proxy)

## Contributing

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes with appropriate tests
4. Submit a pull request

## License

[Add your license information here]