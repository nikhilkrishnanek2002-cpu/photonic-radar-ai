# Docker Quick Reference - PHOENIX Radar AI

## One-Line Quick Start

```bash
docker compose up --build
```

**That's it!** Services will be available at:
- API: http://localhost:8000
- UI: http://localhost:8501

---

## Essential Commands

### 🚀 Getting Started

```bash
# Build and start all services
docker compose up --build

# Start services (no rebuild)
docker compose up -d

# View running services
docker compose ps

# View logs (live)
docker compose logs -f

# Stop services
docker compose stop

# Stop and remove everything
docker compose down
```

### 🔧 Management

```bash
# Restart services
docker compose restart

# Rebuild images
docker compose build --no-cache

# Service info
docker compose ps
docker compose config
docker compose inspect <service>
```

### 📋 Logs & Debugging

```bash
# All services logs
docker compose logs

# Specific service logs (live)
docker compose logs -f backend
docker compose logs -f streamlit

# Last 50 lines
docker compose logs --tail 50

# With timestamps
docker compose logs --timestamps

# Save to file
docker compose logs > logs.txt
```

### 🖥️ Container Access

```bash
# Enter container shell
docker compose exec backend bash
docker compose exec streamlit bash

# Run command in container
docker compose exec backend python -c "import sys; print(sys.version)"

# Copy files out of container
docker compose cp backend:/app/logs ./local-logs
```

### 📊 Monitoring

```bash
# Real-time resource usage
docker stats

# Service health check
docker compose exec backend curl http://localhost:5000/health

# View events
docker compose events
```

### 🧹 Cleanup

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Full cleanup (⚠️ removes all)
docker system prune -a --volumes
```

---

## Using the Management Script

Skip all above! Use the included script:

```bash
# Make executable (one time)
chmod +x docker-manage.sh

# Common operations
./docker-manage.sh start              # Start services
./docker-manage.sh stop               # Stop services
./docker-manage.sh logs               # View logs
./docker-manage.sh health             # Check health
./docker-manage.sh shell-backend      # Enter backend
./docker-manage.sh test               # Test endpoints
./docker-manage.sh dev                # Development mode
./docker-manage.sh prod               # Production mode
./docker-manage.sh help               # All commands
```

---

## Configuration

### Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit with your settings
nano .env

# Auto-loaded by docker compose
docker compose up
```

### Development Mode

```bash
# Auto-loaded via docker-compose.override.yml
docker compose up

# Features:
# - Source code mounted (hot reload)
# - Debug logging enabled
# - No auto-restart on error
```

### Production Mode

```bash
# Multi-file compose (overrides default)
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               up -d

# Or use script
./docker-manage.sh prod

# Features:
# - Resource limits enforced
# - Warning-level logging
# - Auto-restart on failure
# - Health monitoring
```

---

## Troubleshooting Quick Fixes

### Port Already in Use

```bash
# Find process on port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port (edit docker-compose.yml)
# ports:
#   - "8001:5000"
```

### Services Won't Start

```bash
# Check Docker daemon
docker ps

# Clean rebuild
docker compose down -v
docker compose build --no-cache
docker compose up

# Check logs
docker compose logs
```

### Can't Connect to API

```bash
# Verify backend is running
docker compose ps

# Check if listening
curl http://localhost:8000/health

# Check logs
docker compose logs backend

# Verify port mapping
docker compose port backend 5000
```

### Out of Disk Space

```bash
# Check usage
docker system df

# Clean up
docker system prune -a --volumes
```

---

## Access Services

### Backend API

```bash
# Health check
curl http://localhost:8000/health

# Example response:
# {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}
```

### Streamlit Dashboard

```bash
# Open in browser
http://localhost:8501

# Or from terminal
open http://localhost:8501  # macOS
xdg-open http://localhost:8501  # Linux
start http://localhost:8501  # Windows
```

---

## Common Workflows

### Development (Hot Reload)

```bash
# 1. Start services
docker compose up

# 2. Edit code in IDE
vim photonic-radar-ai/ui/dashboard.py

# 3. Save file (auto-loads)

# 4. Refresh browser to see changes

# 5. View logs
docker compose logs -f
```

### Debugging

```bash
# 1. Enable debug logging
# Edit .env: LOG_LEVEL=DEBUG

# 2. Restart
docker compose restart

# 3. Watch logs
docker compose logs -f backend

# 4. Access container
docker compose exec backend bash

# 5. Check files
ls -la /app/logs
```

### Testing Endpoints

```bash
# Test API health
curl -v http://localhost:8000/health

# Test from within network
docker compose exec streamlit curl http://backend:5000/health

# Get headers
curl -i http://localhost:8000/health
```

### Performance Tuning

```bash
# View resource usage
docker stats --no-stream

# If high, edit docker-compose.yml or docker-compose.prod.yml
# deploy:
#   resources:
#     limits:
#       cpus: '2'
#       memory: 2G

# Restart with new limits
docker compose up -d
```

---

## Docker File Structure

```
Project Root (.)
├── Dockerfile                  # Image definition
├── docker-compose.yml          # Service orchestration
├── docker-compose.override.yml # Development (auto-load)
├── docker-compose.prod.yml     # Production (manual load)
├── .dockerignore               # Excludes from build
├── docker-manage.sh            # Management script
├── .env.example                # Environment template
├── .env                        # [User created] Environment config
│
├── runtime/                    # [Created by compose] IPC
├── logs/                       # [Created by compose] Logs
│   ├── backend/
│   └── streamlit/
│
└── photonic-radar-ai/          # Main application
    ├── requirements.txt
    ├── main.py
    └── ui/dashboard.py
```

---

## Advanced Commands

### Multi-Compose Files

```bash
# Development + custom config
docker compose -f docker-compose.yml \
               -f docker-compose.override.yml \
               -f my-custom.yml \
               up

# Production + monitoring
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               -f docker-compose.monitoring.yml \
               up -d
```

### Environment Overrides

```bash
# Override via command line
docker compose up -e LOG_LEVEL=DEBUG

# Override via .env
echo "LOG_LEVEL=DEBUG" > .env
docker compose up

# Override in -f file
services:
  backend:
    environment:
      LOG_LEVEL: DEBUG
```

### Scaling (Advanced)

```bash
# Run multiple instances (requires load balancing)
docker compose up -d --scale backend=3

# View scaled services
docker compose ps
```

### Network Inspection

```bash
# List networks
docker network ls

# Inspect network
docker network inspect phoenix-network

# Test inter-container connectivity
docker compose exec streamlit ping backend
docker compose exec backend ping streamlit
```

---

## Performance Tips

1. **Use `.dockerignore`** - Reduces build context
2. **Layer caching** - Put stable RUN commands first in Dockerfile
3. **Minimal base image** - python:3.11-slim vs python:3.11
4. **Resource limits** - Prevent runaway containers
5. **Log rotation** - Prevents disk fill (set in docker-compose.prod.yml)
6. **Volume type** - Named volumes faster than bind mounts

---

## Environment Variables

### Key Variables

```env
# Backend
API_HOST=0.0.0.0
API_PORT=5000
LOG_LEVEL=INFO

# Streamlit
API_URL=http://backend:5000
STREAMLIT_SERVER_HEADLESS=true

# Python
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### See All Used

```bash
# From .env file
cat .env

# From container
docker compose exec backend env | sort

# From image
docker inspect <image-id> | grep -i env
```

---

## Security Best Practices

- ✅ Use non-root user (see Dockerfile)
- ✅ Minimize base image (python:3.11-slim)
- ✅ Don't commit .env (use .env.example)
- ✅ Change SECRET_KEY in production
- ✅ Use read-only volumes where possible
- ✅ Enable health checks
- ✅ Set resource limits

---

## External Resources

- **Docker Docs:** https://docs.docker.com
- **Docker Compose Spec:** https://docs.docker.com/compose/compose-file/
- **Best Practices:** https://docs.docker.com/develop/dev-best-practices/

---

## Need More Help?

```bash
# Show full documentation
cat DOCKER_DEPLOYMENT.md

# List all compose commands
docker compose --help

# Show specific command help
docker compose up --help

# View current configuration
docker compose config
```

---

**Last Updated:** 2024
**Quick Start Status:** ✅ Ready in 1 command
