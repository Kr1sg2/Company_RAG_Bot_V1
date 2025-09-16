# OPERATIONS.md

## Production Operations Guide

This document covers deployment, monitoring, and maintenance of the Company RAG Bot in production environments.

### Reverse Proxy Configuration

The application is designed to run behind a reverse proxy that handles routing and SSL termination.

#### Nginx Configuration Example

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Frontend (static files)
    location / {
        proxy_pass http://localhost:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:8601/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
    }
}
```

#### Cloudflare Tunnel Alternative

For simpler deployment, you can use Cloudflare Tunnel:

```bash
# Install cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Authenticate and create tunnel
cloudflared tunnel login
cloudflared tunnel create company-rag-bot

# Configure tunnel (cloudflared.yml)
tunnel: <tunnel-id>
credentials-file: /home/user/.cloudflared/<tunnel-id>.json
ingress:
  - hostname: your-domain.com
    service: http://localhost:8082
  - hostname: api.your-domain.com  
    service: http://localhost:8601
  - service: http_status:404
```

### Backup Strategy

#### Critical Data to Back Up

1. **Vector Database**: `backend/chroma_db/`
   - Contains all document embeddings
   - Recreating requires reprocessing all documents
   - Backup frequency: Daily

2. **SQLite Databases**: `*.sqlite`, `*.db` files
   - Application state and metadata
   - Backup frequency: Daily

3. **Configuration**: Environment files and settings
   - `.env` files (excluding secrets)
   - Application settings stored in `backend/storage/`

#### Backup Commands

```bash
# Create backup directory with timestamp
BACKUP_DIR="/backups/company-rag-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup vector database
tar -czf "$BACKUP_DIR/chroma_db.tar.gz" backend/chroma_db/

# Backup SQLite databases
find . -name "*.sqlite*" -o -name "*.db" | tar -czf "$BACKUP_DIR/databases.tar.gz" -T -

# Backup application storage
tar -czf "$BACKUP_DIR/storage.tar.gz" backend/storage/

# Upload to cloud storage (example with aws cli)
aws s3 sync "$BACKUP_DIR" s3://your-backup-bucket/company-rag/
```

### Monitoring and Health Checks

#### Health Endpoints

- **Backend**: `GET /health` returns `{"status": "ok"}`
- **Docker**: Health checks configured in compose files
- **Monitoring**: Use tools like Uptime Robot or Pingdom

#### Log Monitoring

```bash
# View backend logs
docker logs company_rag_backend -f

# View frontend logs  
docker logs company_rag_frontend -f

# System logs
journalctl -u docker -f
```

#### Key Metrics to Monitor

- **Response Time**: Average API response times
- **Error Rate**: HTTP 4xx/5xx responses
- **Memory Usage**: Backend memory consumption
- **Disk Usage**: Vector database growth
- **OpenAI API Usage**: Token consumption and costs

### Maintenance Tasks

#### Regular Updates

1. **Weekly**: Review dependency audit results
2. **Monthly**: Update Docker images for security patches
3. **Quarterly**: Review and update documentation

#### Document Reindexing

When documents are updated:

```bash
# Stop the backend service
docker compose -f infra/docker-compose.prod.yml stop backend

# Clear vector database
rm -rf backend/chroma_db/*

# Restart and trigger reindexing
docker compose -f infra/docker-compose.prod.yml up -d

# Monitor logs for reindexing completion
docker logs company_rag_backend -f
```

### Troubleshooting

#### Common Issues

1. **Backend fails to start**: Check environment variables and dependencies
2. **No search results**: Verify ChromaDB data and OpenAI API connectivity  
3. **Slow responses**: Check OpenAI API limits and backend resource usage
4. **CORS errors**: Verify allowed origins configuration

#### Debug Commands

```bash
# Check container status
docker compose ps

# View detailed logs
docker compose logs backend --tail=100

# Test health endpoints
curl http://localhost:8601/health
curl http://localhost:8082/

# Check environment variables
docker exec company_rag_backend env | grep -E "(OPENAI|LEXA)"
```