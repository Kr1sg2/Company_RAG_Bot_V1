# Lexa AI V2 — Service Management

Complete guide to running Lexa AI as system services in development and production.

---

## Table of Contents

1. [Service Overview](#service-overview)
2. [Systemd Units](#systemd-units)
3. [Service Management](#service-management)
4. [Port Configuration](#port-configuration)
5. [Log Management](#log-management)
6. [Auto-Start on Boot](#auto-start-on-boot)
7. [Development vs Production](#development-vs-production)
8. [Rollback Procedures](#rollback-procedures)

---

## Service Overview

Lexa AI V2 runs as multiple services:

| Service Name | Purpose | Port | User | Auto-Start |
|--------------|---------|------|------|------------|
| `lexa-backend.service` | FastAPI backend (main app) | 8601 | www-data | Yes |
| `ai-bridge-watcher.service` | File watcher (optional) | N/A | bizbots24 | Optional |
| Frontend (dev) | Vite dev server | 8082 | bizbots24 | No (dev only) |
| Frontend (prod) | Nginx static files | 80/443 | www-data | Yes (via nginx) |

**Production Stack:**
- Backend: Systemd service → Uvicorn → FastAPI
- Frontend: Nginx → Static React build
- Watcher: Systemd service → Python watchdog → Indexer

**Development Stack:**
- Backend: tmux → Uvicorn → FastAPI
- Frontend: tmux → Vite dev server
- Watcher: tmux → Python watchdog → Indexer

---

## Systemd Units

### Backend Service

**File:** `deployment/lexa-backend.service`

**Unit Configuration:**
```ini
[Unit]
Description=Lexa AI Backend Service
Documentation=https://github.com/your-org/lexa-ai
After=network.target network-online.target
Wants=network-online.target
Requires=local-fs.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/lexa/backend

# Environment file with all configuration
EnvironmentFile=/opt/lexa/config/lexa.env

# Python virtual environment path
Environment="PATH=/opt/lexa/backend/.venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Service command with production settings
ExecStart=/opt/lexa/backend/.venv/bin/uvicorn app:app \
    --host 127.0.0.1 \
    --port 8601 \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-log \
    --log-level info

# Health check
ExecStartPost=/bin/sleep 3
ExecStartPost=/bin/bash -c 'curl -f http://127.0.0.1:8601/api/health || exit 1'

# Restart configuration
Restart=always
RestartSec=5
StartLimitInterval=60s
StartLimitBurst=3

# Resource limits
MemoryMax=2G
MemoryHigh=1.5G
CPUQuota=200%

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/lexa/data /opt/lexa/logs
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lexa-backend

# Environment variables
Environment="PYTHONPATH=/opt/lexa/backend"
Environment="PYTHONUNBUFFERED=1"
Environment="LEXA_LOG_LEVEL=INFO"

[Install]
WantedBy=multi-user.target
```

**Key Features:**
- **Health Check:** Automatically verifies backend is responding after start
- **Auto-Restart:** Restarts on failure with exponential backoff
- **Resource Limits:** Caps memory at 2GB, CPU at 200%
- **Security:** Read-only system, isolated temp, no privilege escalation
- **Workers:** Runs 2 Uvicorn workers for concurrent request handling

### Watcher Service

**File:** `deployment/ai-bridge-watcher.service`

**Unit Configuration:**
```ini
[Unit]
Description=AI Bridge Inbox Watcher
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=bizbots24
Group=bizbots24
EnvironmentFile=/etc/lexa/ai-bridge.env
ExecStart=/bin/bash /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/Backend_FastAPI/bridge_watcher/watch_inbox.sh
Restart=on-failure
RestartSec=2
Nice=5

# Hardening
NoNewPrivileges=yes
PrivateTmp=yes
ReadWritePaths=/home/bizbots24/ai-bridge/inbox
ReadWritePaths=/home/bizbots24/ai-bridge/inbox/.processed

[Install]
WantedBy=multi-user.target
```

**Key Features:**
- **File Monitoring:** Watches inbox directory for new documents
- **Low Priority:** Nice value 5 to not interfere with backend
- **Isolated Writes:** Only inbox and processed directories writable

---

## Service Management

### Starting Services

**Backend:**
```bash
# Start backend service
sudo systemctl start lexa-backend.service

# Verify it started
sudo systemctl status lexa-backend.service

# Check health endpoint
curl http://localhost:8601/api/health
```

**Watcher:**
```bash
# Start watcher service
sudo systemctl start ai-bridge-watcher.service

# Verify it started
sudo systemctl status ai-bridge-watcher.service
```

### Stopping Services

```bash
# Stop backend
sudo systemctl stop lexa-backend.service

# Stop watcher
sudo systemctl stop ai-bridge-watcher.service

# Stop all Lexa services
sudo systemctl stop lexa-backend.service ai-bridge-watcher.service
```

### Restarting Services

**Graceful Restart:**
```bash
# Restart backend (waits for active requests to finish)
sudo systemctl restart lexa-backend.service

# Reload configuration without restart (if supported)
sudo systemctl reload lexa-backend.service
```

**Force Restart:**
```bash
# Kill and restart immediately
sudo systemctl kill -s SIGKILL lexa-backend.service
sudo systemctl start lexa-backend.service
```

### Checking Status

```bash
# Full status with recent logs
sudo systemctl status lexa-backend.service

# Check if service is active
sudo systemctl is-active lexa-backend.service

# Check if service is enabled on boot
sudo systemctl is-enabled lexa-backend.service

# Show service configuration
sudo systemctl show lexa-backend.service

# List all Lexa services
sudo systemctl list-units | grep lexa
```

---

## Port Configuration

### Backend Ports

| Port | Service | Bind Address | Access | Purpose |
|------|---------|--------------|--------|---------|
| 8601 | Backend API | 127.0.0.1 | Local only | FastAPI application |
| 8082 | Frontend (dev) | 0.0.0.0 | All interfaces | Vite dev server |
| 80 | Frontend (prod) | 0.0.0.0 | Public | Nginx HTTP |
| 443 | Frontend (prod) | 0.0.0.0 | Public | Nginx HTTPS |

**Port Forwarding:**

For production, Nginx proxies to backend:
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8601/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
}
```

**Firewall Configuration:**

```bash
# Allow frontend access (production)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow frontend dev server (development only)
sudo ufw allow 8082/tcp

# Backend should NOT be exposed directly
# Only accessible via Nginx proxy
```

**Checking Port Usage:**
```bash
# Check if port is in use
sudo lsof -i :8601
sudo netstat -tlnp | grep 8601

# Check all Lexa ports
sudo ss -tlnp | grep -E '8601|8082'
```

---

## Log Management

### Systemd Journal Logs

**Backend Logs:**
```bash
# View recent logs
sudo journalctl -u lexa-backend.service -n 50

# Follow logs in real-time
sudo journalctl -u lexa-backend.service -f

# View logs since specific time
sudo journalctl -u lexa-backend.service --since "2025-10-22 10:00:00"

# View logs for last hour
sudo journalctl -u lexa-backend.service --since "1 hour ago"

# Search logs for errors
sudo journalctl -u lexa-backend.service | grep ERROR

# Export logs to file
sudo journalctl -u lexa-backend.service > lexa-backend.log
```

**Watcher Logs:**
```bash
# View watcher logs
sudo journalctl -u ai-bridge-watcher.service -n 50

# Follow watcher activity
sudo journalctl -u ai-bridge-watcher.service -f
```

**All Lexa Services:**
```bash
# Combined logs from all services
sudo journalctl -u lexa-backend.service -u ai-bridge-watcher.service -f
```

### Log Locations

| Log Type | Location | Rotation | Format |
|----------|----------|----------|--------|
| Systemd journal | `/var/log/journal/` | Automatic (max 4G) | Binary (use journalctl) |
| Backend logs | Systemd journal | N/A | Structured JSON |
| Uvicorn access | Systemd journal | N/A | Plain text |
| Application logs | stdout → journal | N/A | Python logging |

### Log Rotation

**Journal Rotation:**
```bash
# Check journal disk usage
sudo journalctl --disk-usage

# Rotate journals now
sudo journalctl --rotate

# Clean old journals (keep last 3 days)
sudo journalctl --vacuum-time=3d

# Clean old journals (keep max 500MB)
sudo journalctl --vacuum-size=500M
```

**Custom Log Files:**

If you configure file-based logging:
```bash
# /etc/logrotate.d/lexa-backend
/opt/lexa/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload lexa-backend.service > /dev/null 2>&1 || true
    endscript
}
```

---

## Auto-Start on Boot

### Enable Services

**Backend:**
```bash
# Enable backend to start on boot
sudo systemctl enable lexa-backend.service

# Verify it's enabled
sudo systemctl is-enabled lexa-backend.service
# Output: enabled
```

**Watcher:**
```bash
# Enable watcher to start on boot
sudo systemctl enable ai-bridge-watcher.service

# Verify
sudo systemctl is-enabled ai-bridge-watcher.service
```

**Enable and Start:**
```bash
# Enable and start in one command
sudo systemctl enable --now lexa-backend.service
sudo systemctl enable --now ai-bridge-watcher.service
```

### Disable Services

```bash
# Disable backend (won't start on boot)
sudo systemctl disable lexa-backend.service

# Disable and stop immediately
sudo systemctl disable --now lexa-backend.service
```

### Check Boot Order

```bash
# Show boot dependencies
sudo systemd-analyze critical-chain lexa-backend.service

# Show which services start Lexa
sudo systemctl list-dependencies lexa-backend.service --reverse
```

---

## Development vs Production

### Development Mode (tmux)

**Running with tmux:**
```bash
# Start development environment
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2

# Create tmux session
tmux new-session -s lexa

# Window 0: Backend
source .venv/bin/activate
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8601

# Window 1 (Ctrl-B C): Frontend
cd frontend
npm run dev

# Window 2 (Ctrl-B C): Watcher
source .venv/bin/activate
cd backend
python -m indexer.watch

# Detach: Ctrl-B D
# Reattach: tmux attach -t lexa
```

**Benefits:**
- Code hot-reloading
- Easy console access
- Interactive debugging
- Quick iteration
- No sudo required

**Limitations:**
- Not persistent across reboots
- No automatic restart on crash
- No resource limits
- Manual log management

### Production Mode (systemd)

**Deploying to Production:**
```bash
# 1. Install service files
sudo cp deployment/lexa-backend.service /etc/systemd/system/
sudo cp deployment/ai-bridge-watcher.service /etc/systemd/system/

# 2. Create environment file
sudo mkdir -p /opt/lexa/config
sudo nano /opt/lexa/config/lexa.env
# Add:
# OPENAI_API_KEY=sk-...
# ADMIN_PASSWORD=...
# SECRET_KEY=...

# 3. Set permissions
sudo chmod 600 /opt/lexa/config/lexa.env

# 4. Reload systemd
sudo systemctl daemon-reload

# 5. Enable and start
sudo systemctl enable --now lexa-backend.service

# 6. Verify
sudo systemctl status lexa-backend.service
curl http://localhost:8601/api/health
```

**Benefits:**
- Auto-start on boot
- Auto-restart on crash
- Resource limits enforced
- Security hardening
- Centralized logging
- Monitoring integration

**Limitations:**
- Requires sudo for changes
- No hot-reloading
- Slower iteration cycle
- More complex debugging

### Switching Between Modes

**Development → Production:**
```bash
# 1. Stop tmux services
tmux kill-session -t lexa

# 2. Start systemd services
sudo systemctl start lexa-backend.service

# 3. Verify
sudo systemctl status lexa-backend.service
```

**Production → Development:**
```bash
# 1. Stop systemd services
sudo systemctl stop lexa-backend.service

# 2. Start tmux
tmux new-session -s lexa
# ... run backend manually
```

---

## Rollback Procedures

### Code Rollback

**Using Git:**
```bash
# 1. Stop services
sudo systemctl stop lexa-backend.service

# 2. Checkout previous version
cd /opt/lexa
git log --oneline -10  # Find commit to rollback to
git checkout <commit-hash>

# 3. Reinstall dependencies (if changed)
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# 4. Restart services
sudo systemctl start lexa-backend.service

# 5. Verify
curl http://localhost:8601/api/health
sudo journalctl -u lexa-backend.service -n 50
```

**Using Branches:**
```bash
# 1. Stop services
sudo systemctl stop lexa-backend.service

# 2. Switch to stable branch
git checkout main  # or production, stable, etc.
git pull origin main

# 3. Reinstall dependencies
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# 4. Restart services
sudo systemctl start lexa-backend.service
```

### Service Configuration Rollback

**Restore Previous Service File:**
```bash
# 1. Find backup
ls -la /etc/systemd/system/lexa-backend.service*

# 2. Restore from backup
sudo cp /etc/systemd/system/lexa-backend.service.backup /etc/systemd/system/lexa-backend.service

# 3. Reload systemd
sudo systemctl daemon-reload

# 4. Restart service
sudo systemctl restart lexa-backend.service
```

**Using Git for Service Files:**
```bash
# 1. Rollback service file in repo
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2
git checkout HEAD~1 -- deployment/lexa-backend.service

# 2. Copy to systemd
sudo cp deployment/lexa-backend.service /etc/systemd/system/

# 3. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart lexa-backend.service
```

### Database Rollback

**Restore ChromaDB Backup:**
```bash
# 1. Stop backend
sudo systemctl stop lexa-backend.service

# 2. Backup current database
mv backend/chroma_db backend/chroma_db.broken

# 3. Restore from backup
cp -r backend/chroma_db.backup backend/chroma_db

# 4. Restart backend
sudo systemctl start lexa-backend.service

# 5. Verify
curl http://localhost:8601/api/health
```

See [RUNBOOK.md](RUNBOOK.md#backup-and-restore) for detailed backup procedures.

### Emergency Procedures

**Complete Service Reset:**
```bash
# 1. Stop all services
sudo systemctl stop lexa-backend.service ai-bridge-watcher.service

# 2. Disable services
sudo systemctl disable lexa-backend.service ai-bridge-watcher.service

# 3. Remove service files
sudo rm /etc/systemd/system/lexa-backend.service
sudo rm /etc/systemd/system/ai-bridge-watcher.service

# 4. Reload systemd
sudo systemctl daemon-reload

# 5. Clear journal logs (optional)
sudo journalctl --rotate
sudo journalctl --vacuum-time=1s

# 6. Reinstall from scratch
cd /home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2
# Follow RUNBOOK.md setup steps
```

**Rollback Checklist:**

- [ ] Stop affected services
- [ ] Backup current state (code, config, database)
- [ ] Identify target rollback version/commit
- [ ] Checkout code or restore files
- [ ] Reinstall dependencies if requirements.txt changed
- [ ] Reload systemd if service files changed
- [ ] Restart services
- [ ] Verify health endpoint responds
- [ ] Check logs for errors
- [ ] Test key functionality (chat query)
- [ ] Monitor for 10 minutes
- [ ] Document rollback in incident log

---

## Monitoring and Alerting

### Health Checks

**Manual Health Check:**
```bash
# Backend health
curl -f http://localhost:8601/api/health

# Expected response:
# {"status":"healthy","timestamp":"2025-10-22T23:00:00Z"}
```

**Automated Health Monitoring:**

Create systemd timer for periodic checks:
```bash
# /etc/systemd/system/lexa-health-check.service
[Unit]
Description=Lexa Backend Health Check

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -f http://localhost:8601/api/health
User=nobody
```

```bash
# /etc/systemd/system/lexa-health-check.timer
[Unit]
Description=Lexa Backend Health Check Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

### Resource Monitoring

```bash
# CPU and memory usage
sudo systemctl status lexa-backend.service

# Detailed resource stats
systemd-cgtop | grep lexa

# Check against limits
sudo systemctl show lexa-backend.service | grep -E 'Memory|CPU'
```

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u lexa-backend.service -n 50
```

**Common causes:**
- Missing environment file: `sudo ls -la /opt/lexa/config/lexa.env`
- Wrong permissions: `sudo chown www-data:www-data /opt/lexa -R`
- Port already in use: `sudo lsof -i :8601`
- Missing dependencies: `source .venv/bin/activate && pip list`
- Python path issues: Check `PYTHONPATH` in service file

### Service Crashes Immediately

**Check exit status:**
```bash
sudo systemctl status lexa-backend.service
# Look for "Main process exited, code=exited, status=1/FAILURE"
```

**Debug with manual start:**
```bash
# Run as service user
sudo -u www-data bash
cd /opt/lexa/backend
source .venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8601
# Watch for errors
```

### Service Doesn't Auto-Restart

**Check restart configuration:**
```bash
sudo systemctl show lexa-backend.service | grep Restart
# Should show: Restart=always
```

**Check restart limits:**
```bash
sudo systemctl show lexa-backend.service | grep StartLimit
# StartLimitBurst=3 means max 3 restarts in StartLimitInterval
```

**Reset failed state:**
```bash
sudo systemctl reset-failed lexa-backend.service
sudo systemctl start lexa-backend.service
```

### Port Already in Use

```bash
# Find process using port 8601
sudo lsof -i :8601

# Kill the process
sudo kill <PID>

# Or kill all uvicorn processes
sudo pkill -f uvicorn
```

### Permission Denied Errors

```bash
# Fix ownership
sudo chown -R www-data:www-data /opt/lexa/data
sudo chown -R www-data:www-data /opt/lexa/logs

# Fix SELinux context (if applicable)
sudo chcon -R -t httpd_sys_rw_content_t /opt/lexa/data
```

---

## See Also

- [RUNBOOK.md](RUNBOOK.md) - Complete operational procedures
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Detailed troubleshooting guide
- [Systemd Documentation](https://www.freedesktop.org/software/systemd/man/)
