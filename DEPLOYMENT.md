# Production Deployment Guide

## Prerequisites

### System Requirements
- Ubuntu/Debian Linux server
- Python 3.12+
- Node.js 18+
- Nginx (reverse proxy)
- Systemd (service management)
- 4GB+ RAM (for embedding generation)
- 20GB+ disk space (for document storage and vector database)

### System Packages
```bash
sudo apt update
sudo apt install -y \
  python3.12 python3.12-venv python3-pip \
  nodejs npm \
  nginx \
  poppler-utils tesseract-ocr ghostscript \
  supervisor
```

## Directory Structure

```
/opt/lexa/
├── backend/                 # Backend FastAPI application
├── frontend/               # Frontend built assets
├── data/
│   ├── documents/          # Document storage
│   ├── chroma_db/         # Vector database
│   └── cache/             # Processing cache
├── logs/                   # Application logs
├── config/                 # Configuration files
└── scripts/                # Management scripts
```

## Backend Deployment

### 1. Application Setup
```bash
sudo mkdir -p /opt/lexa/{backend,frontend,data,logs,config,scripts}
sudo chown -R www-data:www-data /opt/lexa

# Copy backend files
sudo cp -r Backend_FastAPI/* /opt/lexa/backend/

# Create virtual environment
cd /opt/lexa/backend
sudo -u www-data python3.12 -m venv .venv
sudo -u www-data .venv/bin/pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# /opt/lexa/config/lexa.env
OPENAI_API_KEY=your_openai_api_key_here
LEXA_WATCH_DIR=/opt/lexa/data/documents
LEXA_CACHE_DIR=/opt/lexa/data/cache
LEXA_CHROMA_PATH=/opt/lexa/data/chroma_db
ADMIN_PASSWORD=your_secure_admin_password
SECRET_KEY=your_secret_key_change_this
PUBLIC_HOST=https://yourdomain.com
LEXA_CHUNK_CHARS=1200
LEXA_CHUNK_OVERLAP=0.25
LEXA_DISABLE_OCR=1
LEXA_DISABLE_TABLES=1
LEXA_SKIP_IMAGE_ONLY=1
```

### 3. Systemd Service
```bash
# /etc/systemd/system/lexa-backend.service
[Unit]
Description=Lexa AI Backend
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/lexa/backend
Environment=PATH=/opt/lexa/backend/.venv/bin
EnvironmentFile=/opt/lexa/config/lexa.env
ExecStart=/opt/lexa/backend/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8601 --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 4. Start Backend Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable lexa-backend
sudo systemctl start lexa-backend
sudo systemctl status lexa-backend
```

## Frontend Deployment

### 1. Build Frontend
```bash
cd frontend
npm ci --production=false
npm run build

# Copy built assets
sudo cp -r dist/* /opt/lexa/frontend/
sudo chown -R www-data:www-data /opt/lexa/frontend
```

### 2. Production Environment
```bash
# frontend/.env.production
VITE_API_BASE_URL=https://yourdomain.com
```

## Reverse Proxy Configuration

### Nginx Configuration
```nginx
# /etc/nginx/sites-available/lexa
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # SSL security headers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Frontend static files
    location / {
        root /opt/lexa/frontend;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8601;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # File serving for document access
    location /files/ {
        alias /opt/lexa/data/documents/;
        
        # Security: prevent directory traversal
        location ~ \.\. {
            deny all;
        }
        
        # Cache document files
        expires 1h;
        add_header Cache-Control "public";
    }
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/lexa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Indexer Service

### Systemd Service for Document Processing
```bash
# /etc/systemd/system/lexa-indexer.service
[Unit]
Description=Lexa AI Document Indexer
After=network.target lexa-backend.service
Requires=lexa-backend.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/lexa/backend
Environment=PATH=/opt/lexa/backend/.venv/bin
EnvironmentFile=/opt/lexa/config/lexa.env
ExecStart=/opt/lexa/backend/.venv/bin/python -m indexer.watch
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable lexa-indexer
sudo systemctl start lexa-indexer
```

## Logging & Monitoring

### Log Rotation
```bash
# /etc/logrotate.d/lexa
/opt/lexa/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload lexa-backend
        systemctl reload lexa-indexer
    endscript
}
```

### Monitoring Scripts
```bash
# /opt/lexa/scripts/health-check.sh
#!/bin/bash
set -e

# Check backend health
if ! curl -f http://127.0.0.1:8601/api/health > /dev/null 2>&1; then
    echo "Backend health check failed"
    systemctl restart lexa-backend
    sleep 5
fi

# Check disk space
USAGE=$(df /opt/lexa/data | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$USAGE" -gt 85 ]; then
    echo "Warning: Disk usage is ${USAGE}%"
    # Cleanup old cache files
    find /opt/lexa/data/cache -name "*.cache" -mtime +7 -delete
fi

echo "Health check completed successfully"
```

### Cron Jobs
```bash
# /etc/cron.d/lexa
# Health check every 5 minutes
*/5 * * * * www-data /opt/lexa/scripts/health-check.sh >> /opt/lexa/logs/health.log 2>&1

# Backup vector database daily
0 2 * * * www-data tar -czf /opt/lexa/backups/chroma_db_$(date +\%Y\%m\%d).tar.gz -C /opt/lexa/data chroma_db/
```

## SSL/TLS Configuration

### Let's Encrypt (Recommended)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo systemctl enable certbot.timer
```

## Security Hardening

### Firewall Configuration
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw deny 8601  # Block direct backend access
```

### File Permissions
```bash
sudo chmod -R 750 /opt/lexa
sudo chmod -R 640 /opt/lexa/config
sudo chmod 600 /opt/lexa/config/lexa.env
```

### Application Security
- Change default admin password
- Use strong SECRET_KEY
- Implement rate limiting in Nginx
- Regular security updates

## Backup Strategy

### Database Backup
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf /opt/lexa/backups/chroma_db_$DATE.tar.gz -C /opt/lexa/data chroma_db/
find /opt/lexa/backups -name "chroma_db_*.tar.gz" -mtime +30 -delete
```

### Document Backup
```bash
# Weekly document backup
rsync -av /opt/lexa/data/documents/ /backup/location/documents/
```

## Performance Tuning

### Uvicorn Workers
```bash
# Adjust worker count based on CPU cores
ExecStart=/opt/lexa/backend/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8601 --workers 4
```

### Nginx Optimization
```nginx
# In nginx.conf http block
worker_processes auto;
worker_connections 1024;

# Gzip compression
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status lexa-backend
sudo systemctl status lexa-indexer
sudo journalctl -u lexa-backend -f
```

### Common Issues
1. **Backend won't start**: Check environment file and OpenAI API key
2. **No embeddings**: Verify OpenAI API key and network connectivity
3. **Files not indexed**: Check directory permissions and indexer service
4. **High memory usage**: Reduce chunk size or disable OCR

### Manual Restart
```bash
sudo systemctl restart lexa-backend
sudo systemctl restart lexa-indexer
sudo systemctl reload nginx
```