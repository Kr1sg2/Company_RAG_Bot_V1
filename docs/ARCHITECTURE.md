# ARCHITECTURE.md

## System Architecture

The Company RAG Bot follows a modern web application architecture with a React frontend, FastAPI backend, and vector database for document retrieval.

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Reverse Proxy  │    │   Backend       │
│   (React/Vite)  │───▶│   (Nginx/CF)     │───▶│   (FastAPI)     │
│   Port 8080/80  │    │   /api/* → 8601  │    │   Port 8601     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │  Vector Store   │
                                               │  (ChromaDB)     │
                                               │  backend/       │
                                               │  chroma_db/     │
                                               └─────────────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │  External LLM   │
                                               │  (OpenAI API)   │
                                               └─────────────────┘
```

### Component Details

#### Frontend (React + Vite)
- **Technology**: React 19, TypeScript, Vite, Tailwind CSS
- **Responsibilities**: User interface, query input, response display
- **Development**: Vite dev server with proxy to backend on `/api`
- **Production**: Static files served by Nginx

#### Backend (FastAPI)
- **Technology**: Python 3.11, FastAPI, uvicorn
- **Responsibilities**: 
  - Query processing and retrieval
  - Vector search in ChromaDB
  - LLM integration for answer generation
  - Source attribution with page numbers
- **Key Modules**:
  - `app.py`: Main FastAPI application
  - `lexa_app/`: Core business logic modules
  - `lexa_app/retrieval.py`: Enhanced search functionality

#### Vector Database (ChromaDB)
- **Location**: `backend/chroma_db/`
- **Purpose**: Stores document embeddings for semantic search
- **Content**: Company documents chunked and indexed

#### External Services
- **LLM Provider**: OpenAI API (configurable base URL and model)
- **Required for**: Answer generation and query understanding

### Data Flow

1. User submits query through frontend
2. Frontend sends request to `/api/chat` via proxy
3. Backend processes query using enhanced search
4. ChromaDB performs vector similarity search
5. Relevant chunks retrieved with metadata (file, page)
6. LLM generates answer based on retrieved context
7. Response returned with answer and source citations
8. Frontend displays result with clickable source links

### Security Considerations

- **Authentication**: Admin endpoints protected with session tokens
- **CORS**: Configured for specific domains
- **Environment Variables**: Sensitive data in environment files
- **File Access**: Controlled document serving with proper headers