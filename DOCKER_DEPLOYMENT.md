# Docker Deployment Guide for PHOENIX Radar AI

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Prerequisites](#prerequisites)
4. [Installation & Setup](#installation--setup)
5. [Running the Deployment](#running-the-deployment)
6. [Service Access](#service-access)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Development Workflow](#development-workflow)
10. [Production Deployment](#production-deployment)
11. [Common Commands](#common-commands)

---

## Quick Start

**TL;DR for experienced Docker users:**

```bash
# 1. Navigate to project directory
cd /home/nikhil/PycharmProjects/photonic-radar-ai

# 2. (Optional) Configure environment
cp .env.example .env
# Edit .env with your settings (or use defaults)

# 3. Build and run all services
docker compose up --build

# 4. Access services
# API: http://localhost:8000
# UI: http://localhost:8501
```

---

## Architecture Overview

### Service Topology

```
┌─────────────────────────────────────────────────────────────┐
│                   PHOENIX Radar AI (Docker)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐          ┌────────────────────┐    │
│  │   Backend Service  │◄────────►│ Streamlit Service  │    │
│  │  (API + Simulator) │  (IPC)   │   (Dashboard UI)   │    │
│  │   Port: 5000       │          │   Port: 8501       │    │
│  │  Internal Network  │          │  Internal Network  │    │
│  └────────────────────┘          └────────────────────┘    │
│        ▲                                  ▲                 │
│        │                                  │                 │
│        └──────────────────┬───────────────┘                 │
│                           │                                 │
│            Shared Volumes & Network                         │
│          (phoenix-network bridge)                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
        ▲                                        ▲
        │                                        │
   Port 8000                                 Port 8501
(External API)                          (External UI)
```

### Network Isolation

- **Internal Network:** `phoenix-network` (bridge, 172.25.0.0/16)
  - Services communicate via service names (DNS)
  - Backend accessible as `http://backend:5000` from Streamlit
  - Isolated from host network

- **Port Mapping:**
  - Backend: `8000:5000` (external:internal)
  - Streamlit: `8501:8501` (external:internal)

### Shared Resources

| Resource | Purpose | Mounted As |
|----------|---------|-----------|
| `./runtime/` | IPC between services | `/app/runtime` |
| `./logs/` | Service logs | `/app/logs` |
| `phoenix-cache` | Docker volume for pip cache | `/app/.cache` |

### Service Dependencies

```
┌──────────────┐
│  Streamlit   │
│  (depends_on)│
│      │       │
│      ▼       │
│  Backend     │
│ (must be     │
│  healthy)    │
└──────────────┘
```

- Streamlit waits for Backend to pass health check
- Backend has no external dependencies
- Both auto-restart unless manually stopped

---

## Prerequisites

### System Requirements

- **OS:** Linux, macOS, or Windows (WSL2)
- **Disk Space:** 2-3 GB (initial build)
- **RAM:** 2-4 GB minimum (2 GB per service)
- **CPU:** 2+ cores recommended

### Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ (v3.8 format) | Service orchestration |
| Git | any | Project cloning |

### Verification

```bash
# Check Docker installation
docker --version
# Docker version 20.10.0, build ...

# Check Docker Compose installation
docker compose version
# Docker Compose version v2.x.x, build ...

# Check Docker daemon status
docker info
# Should display system info without errors
```

---

## Installation & Setup

### Step 1: Clone or Navigate to Repository

```bash
# Option A: If cloning fresh
git clone <repository-url>
cd photonic-radar-ai

# Option B: If already in project
cd /home/nikhil/PycharmProjects/photonic-radar-ai
```

### Step 2: Verify Project Structure

```bash
# Verify required Docker files exist
ls -la Dockerfile docker-compose.yml .dockerignore

# Expected output:
# Dockerfile (43 lines)
# docker-compose.yml (71 lines)
# .dockerignore (48 lines)
```

### Step 3: Configure Environment (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit with your preferences
nano .env  # or use your editor

# Key variables to consider:
# - LOG_LEVEL (INFO, DEBUG)
# - API_HOST, API_PORT
# - STREAMLIT_* settings
```

### Step 4: Prepare Directories

```bash
# Docker Compose will create automatically, but pre-create for safety
mkdir -p runtime logs/backend logs/streamlit

# Set permissions (optional, for non-root access outside container)
chmod 777 runtime logs/backend logs/streamlit
```

---

## Running the Deployment

### Initial Build & Launch

```bash
# Build images and start all services
docker compose up --build

# Expected output:
# Creating phoenix-network ...
# Creating phoenix-backend ...
# Creating phoenix-streamlit ...
# backend_1  | INFO: Uvicorn running on http://0.0.0.0:5000
# streamlit_1 | You can now view your Streamlit app in your browser.
```

### Background Execution

```bash
# Run services in background (detached mode)
docker compose up -d --build

# Services run in background
# Logs do not display in terminal
# Use 'docker compose logs' to view

# Stop background services later
docker compose down
```

### Startup Sequence

1. **Network Creation:** `phoenix-network` bridge created
2. **Backend Start:** Image built, container started
3. **Health Check:** Backend API tested every 30 seconds
4. **Streamlit Start:** (waits for backend healthy)
5. **Ready:** Both services accepting connections

**Typical Startup Time:** 15-30 seconds (first build) / 5-10 seconds (subsequent)

---

## Service Access

### API Server

**URL:** `http://localhost:8000`

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}
```

### Streamlit Dashboard

**URL:** `http://localhost:8501`

**Access:**
1. Open web browser
2. Navigate to `http://localhost:8501`
3. Dashboard loads with live system visualization

### Logs Access

```bash
# View all service logs
docker compose logs

# Follow backend logs (live)
docker compose logs -f backend

# Follow streamlit logs (live)
docker compose logs -f streamlit

# View last 50 lines of backend logs
docker compose logs --tail=50 backend
```

### Service Status

```bash
# Check running containers
docker compose ps

# Expected output:
# NAME              COMMAND            STATUS         PORTS
# phoenix-backend   python main.py     Up 2 minutes   0.0.0.0:8000->5000/tcp
# phoenix-streamlit streamlit run ...  Up 1 minute    0.0.0.0:8501->8501/tcp
```

---

## Configuration

### Environment Variables

#### Backend Service

```env
# API Configuration
API_HOST=0.0.0.0       # Listen on all interfaces
API_PORT=5000          # Internal port

# Logging
LOG_LEVEL=INFO         # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Python Optimization
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

#### Streamlit Service

```env
# Backend Connection
API_URL=http://backend:5000  # Service name in network

# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_THEME_BASE=dark

# Application
DEMO_MODE=false        # Use synthetic data fallback
DEBUG=false            # Verbose logging
```

### Using .env File

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit configuration
nano .env

# 3. Docker Compose automatically loads .env
docker compose up --build

# 4. Verify variables loaded
docker compose ps  # Should show correct port mapping
```

### Overriding Environment Variables

**Method 1: Command Line**
```bash
docker compose up --build -e LOG_LEVEL=DEBUG
```

**Method 2: .env File**
Edit `.env` before running `docker compose up`

**Method 3: docker-compose.override.yml**
Automatic for development (already provided)

---

## Troubleshooting

### Services Won't Start

#### Problem: `docker: command not found`

```bash
# Solution: Install Docker
# Ubuntu/Debian:
sudo apt-get update && sudo apt-get install docker.io docker-compose

# macOS (with Homebrew):
brew install docker docker-compose
```

#### Problem: `Cannot connect to Docker daemon`

```bash
# Solution: Start Docker daemon
sudo systemctl start docker  # Linux
open --background -a Docker  # macOS

# Or verify daemon is running:
docker ps  # Should not give "Cannot connect" error
```

#### Problem: `Permission denied while trying to connect to Docker socket`

```bash
# Solution: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
docker ps  # Should work now
```

### Port Conflicts

#### Problem: `port is already allocated: listen tcp 0.0.0.0:8000`

```bash
# Solution A: Stop existing service
docker compose down
docker container stop $(docker ps -q)

# Solution B: Use different port
# Edit docker-compose.yml:
# ports:
#   - "8001:5000"  # Changed from 8000

# Solution C: Kill process on port
sudo lsof -i :8000
sudo kill -9 <PID>
```

#### Problem: `Conflict: The container name "/phoenix-backend" is already in use`

```bash
# Solution: Remove existing container
docker compose down
docker container prune  # Removes unused containers

# Then restart
docker compose up -d
```

### Build Failures

#### Problem: `ERROR: failed to build image`

```bash
# Solution 1: Clean rebuild
docker compose down
docker system prune -a  # Remove all unused images
docker compose up --build

# Solution 2: Check Dockerfile syntax
docker build --no-cache .

# Solution 3: Check pip requirements
docker run --rm python:3.11-slim pip install -r requirements.txt
```

### Network Issues

#### Problem: Streamlit can't reach backend API

```bash
# Check network connectivity
docker network ls    # Verify phoenix-network exists
docker network inspect phoenix-network

# Test from Streamlit container
docker compose exec streamlit curl http://backend:5000/health

# If DNS fails, restart services
docker compose restart
```

#### Problem: External client can't reach services

```bash
# Verify port forwarding
docker compose ps  # Check port mappings

# Test connectivity
curl http://localhost:8000/health
curl http://localhost:8501

# If port shows as closed, check firewall
sudo ufw allow 8000  # Ubuntu firewall
sudo ufw allow 8501
```

### Performance Issues

#### Services running slowly

```bash
# Check container resource usage
docker stats

# If CPU/RAM high, increase limits in docker-compose.yml:
# deploy:
#   resources:
#     limits:
#       cpus: '1'
#       memory: 1G

# Restart with new limits
docker compose up -d
```

#### Disk space full

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove specific images
docker rmi <image-id>
```

### Logging & Debugging

```bash
# Enable debug logging
docker compose down
export LOG_LEVEL=DEBUG
docker compose up --build

# View all logs with timestamps
docker compose logs --timestamps

# Export logs to file
docker compose logs > combined-logs.txt
docker compose logs backend > backend.log

# Real-time monitoring
watch -n 1 'docker compose ps && docker stats --no-stream'
```

---

## Development Workflow

### Hot-Reload Development

The project includes `docker-compose.override.yml` for automatic development configuration:

```bash
# Start with development settings (auto-loaded)
docker compose up --build

# Features enabled automatically:
# - Source code mounting (live editing)
# - Debug logging (LOG_LEVEL=DEBUG)
# - No auto-restart on error (better debugging)
# - Streamlit development mode
```

**What this means:**
- Edit files locally, changes reflect immediately in containers
- No rebuild needed for code changes
- Logs show DEBUG-level output
- Faster development iteration

### Making Code Changes

```bash
# 1. Edit code in your IDE
vim photonic-radar-ai/ui/dashboard.py

# 2. Save file (changes immediately visible in container)
# 3. Refresh browser tab to see UI changes
# 4. API automatically restarts on Python errors

# 5. View logs to debug
docker compose logs -f backend
```

### Testing Changes

```bash
# Test specific service
docker compose up -d backend
docker compose logs -f backend

# Test API endpoint
curl http://localhost:8000/health

# Test UI
# Open browser to http://localhost:8501
```

### Debugging Issues

```bash
# Enter running container shell
docker compose exec backend bash

# From within container:
python -c "import photonic_radar_ai; print(photonic_radar_ai.__version__)"
ls -la /app
cat logs/application.log

# Exit container
exit
```

### Switching Configurations

```bash
# Development (auto-loaded by override):
docker compose up --build

# Production (ignores override):
docker compose -f docker-compose.yml up --build

# Custom configuration:
docker compose -f docker-compose.yml \
               -f docker-compose.override.yml \
               -f docker-compose.prod.yml \
               up --build
```

---

## Production Deployment

### Pre-Production Checklist

```bash
# Security review
□ Check .env file (no hardcoded secrets)
□ Verify non-root user in Dockerfile
□ Review CORS settings
□ Update SECRET_KEY in .env

# Performance review
□ Set LOG_LEVEL=INFO (not DEBUG)
□ Enable resource limits
□ Check volume paths accessible
□ Verify network isolation

# Reliability review
□ Health checks configured
□ Restart policies set
□ Logging to persistent volumes
□ Backup strategy for data

# Deployment review
□ .env.prod file created
□ docker-compose.prod.yml ready
□ Secrets management plan
□ Monitoring/alerting setup
```

### Production Environment File

Create `.env.prod`:

```bash
# .env.prod - Production settings (DO NOT commit)

# Security (change these!)
SECRET_KEY=<generate-random-key>
API_HOST=0.0.0.0

# Logging
LOG_LEVEL=WARNING  # Only warnings and errors

# Timeouts
REQUEST_TIMEOUT=60

# Disable debug features
DEBUG=false
DEMO_MODE=false
STREAMLIT_CLIENT_TOOLBAR_MODE=minimal
```

### Production Deployment Command

```bash
# Using production environment
cp .env.prod .env
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               up -d

# Verify services
docker compose ps
curl http://localhost:8000/health
```

### Health Monitoring

```bash
# Check service health
docker compose ps
docker stats

# View error logs
docker compose logs --since 10m backend
docker compose logs --since 10m streamlit

# Alert on failures
docker compose events --filter type=container
```

### Backup & Recovery

```bash
# Backup volumes
docker run --rm -v runtime:/data -v $(pwd):/backup \
  busybox tar czf /backup/runtime-backup.tar.gz -C /data .

# Backup logs
docker run --rm -v logs:/data -v $(pwd):/backup \
  busybox tar czf /backup/logs-backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v runtime:/data -v $(pwd):/backup \
  busybox tar xzf /backup/runtime-backup.tar.gz -C /data
```

---

## Common Commands

### Container Management

```bash
# Start/Stop/Restart
docker compose up -d          # Start (background)
docker compose down           # Stop and remove
docker compose restart        # Restart services
docker compose pause          # Pause services

# View services
docker compose ps             # List running services
docker compose config         # Show effective config

# Logs
docker compose logs [service]  # View logs
docker compose logs -f         # Follow logs
docker compose logs --tail 50  # Last 50 lines
```

### Debugging

```bash
# Execute commands in container
docker compose exec backend bash
docker compose exec streamlit python -c "import sys; print(sys.path)"

# Run one-off command
docker compose run --rm backend python -m pytest tests/

# Copy files
docker compose cp backend:/app/logs local-logs
```

### Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Full system cleanup
docker system prune -a --volumes
```

### Image Management

```bash
# Build image only (don't run)
docker compose build

# Rebuild without cache
docker compose build --no-cache

# View built images
docker images | grep phoenix

# Remove images
docker rmi <image-id>
```

---

## Useful Resources

### Docker Documentation
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker CLI Reference](https://docs.docker.com/engine/reference/commandline/cli/)

### PHOENIX Radar AI
- [README.md](README.md) - Main documentation
- [DASHBOARD_SUMMARY.md](DASHBOARD_SUMMARY.md) - Dashboard overview
- [DEMO_QUICK_START.md](DEMO_QUICK_START.md) - Demo system guide
- [Dockerfile](Dockerfile) - Container image spec
- [docker-compose.yml](docker-compose.yml) - Service orchestration

### Quick Reference Files
- `.env.example` - Environment template
- `docker-compose.override.yml` - Development config
- `.dockerignore` - Build optimization

---

## Getting Help

### Common Issues & Solutions

1. **Services won't start:** Check Docker daemon, ports, disk space
2. **Port conflicts:** Use different ports in .env
3. **Permission denied:** Add user to docker group
4. **Out of disk:** Run `docker system prune -a`
5. **Services slow:** Check `docker stats`

### Support Information

For detailed issues:

```bash
# Collect diagnostic info
docker compose ps
docker compose logs --tail 100
docker system df
docker stats --no-stream

# Save to file for analysis
docker compose logs > debug-logs.txt
docker system df > system-info.txt
```

---

**Last Updated:** 2024
**Deployment Status:** Production-Ready ✅
