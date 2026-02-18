#!/bin/bash
# docker-manage.sh
# Docker management script for PHOENIX Radar AI
# Provides simple commands for common Docker operations

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="phoenix"
BACKEND_SERVICE="backend"
STREAMLIT_SERVICE="streamlit"
DOCKER_COMPOSE_CMD="docker compose"

# Default environment file
ENV_FILE=".env"
COMPOSE_FILE="docker-compose.yml"

print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  PHOENIX Radar AI - Docker Manager   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
}

print_usage() {
    cat << 'EOF'
Usage: ./docker-manage.sh <command> [options]

Commands:
  start          Start all services (no rebuild)
  stop           Stop all services
  restart        Restart all services
  build          Build Docker images only
  up             Build and start all services
  down           Stop and remove services (keeps volumes)
  clean          Remove services, volumes, and cached images
  logs           Show live logs from all services
  logs-backend   Show live logs from backend service
  logs-streamlit Show live logs from streamlit service
  status         Show service status
  health         Check service health
  shell-backend  Open shell in backend container
  shell-streamlit Open shell in streamlit container
  test           Test connectivity (curl health endpoints)
  stats          Show container resource usage
  dev            Start in development mode (override.yml)
  prod           Start in production mode (prod.yml)
  push           Push images to registry (requires configuration)
  help           Show this help message

Examples:
  ./docker-manage.sh start                # Start services
  ./docker-manage.sh logs -f              # Follow logs
  ./docker-manage.sh shell-backend        # Access backend shell
  ./docker-manage.sh test                 # Test endpoints
  ./docker-manage.sh prod                 # Production deployment

EOF
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        exit 1
    fi
    if ! docker ps &> /dev/null; then
        echo -e "${RED}✗ Docker daemon is not running${NC}"
        exit 1
    fi
}

cmd_start() {
    echo -e "${YELLOW}▶ Starting services...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d
    echo -e "${GREEN}✓ Services started${NC}"
    sleep 2
    cmd_status
}

cmd_stop() {
    echo -e "${YELLOW}▶ Stopping services...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE stop
    echo -e "${GREEN}✓ Services stopped${NC}"
}

cmd_restart() {
    echo -e "${YELLOW}▶ Restarting services...${NC}"
    cmd_stop
    sleep 1
    cmd_start
}

cmd_build() {
    echo -e "${YELLOW}▶ Building images...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE build --no-cache
    echo -e "${GREEN}✓ Build complete${NC}"
}

cmd_up() {
    echo -e "${YELLOW}▶ Building and starting services...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE up -d --build
    echo -e "${GREEN}✓ Services running${NC}"
    sleep 3
    cmd_status
}

cmd_down() {
    echo -e "${YELLOW}▶ Stopping and removing services...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down
    echo -e "${GREEN}✓ Services removed${NC}"
}

cmd_clean() {
    echo -e "${YELLOW}▶ Cleaning up Docker resources...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE down -v
    echo -e "${YELLOW}▶ Pruning unused images...${NC}"
    docker system prune -f --volumes
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

cmd_logs() {
    echo -e "${YELLOW}▶ Showing logs...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE logs "$@"
}

cmd_status() {
    echo -e "${BLUE}Service Status:${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE ps
}

cmd_health() {
    echo -e "${BLUE}Checking service health...${NC}"
    
    # Backend health
    if docker compose exec -T backend curl -f http://localhost:5000/health &>/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend${NC} - Healthy (API responding)"
    else
        echo -e "${RED}✗ Backend${NC} - Unhealthy or not running"
    fi
    
    # Streamlit health
    if docker compose exec -T streamlit curl -f http://localhost:8501/_stcore/health &>/dev/null 2>&1; then
        echo -e "${GREEN}✓ Streamlit${NC} - Healthy (UI responding)"
    else
        echo -e "${RED}✗ Streamlit${NC} - Unhealthy or not running"
    fi
}

cmd_shell_backend() {
    echo -e "${YELLOW}▶ Opening shell in backend container...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE exec $BACKEND_SERVICE bash
}

cmd_shell_streamlit() {
    echo -e "${YELLOW}▶ Opening shell in streamlit container...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE exec $STREAMLIT_SERVICE bash
}

cmd_test() {
    echo -e "${BLUE}Testing connectivity...${NC}"
    
    # Test backend API
    echo -n "Backend API (http://localhost:8000/health): "
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
    
    # Test streamlit UI
    echo -n "Streamlit UI (http://localhost:8501): "
    if curl -s http://localhost:8501 > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
    
    # Test inter-service communication
    echo -n "Backend → Streamlit network: "
    if $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE exec -T streamlit curl -f http://backend:5000/health &>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
}

cmd_stats() {
    echo -e "${BLUE}▶ Resource usage (press Ctrl+C to exit)...${NC}"
    docker stats --no-stream
}

cmd_dev() {
    echo -e "${YELLOW}▶ Starting in development mode...${NC}"
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE -f docker-compose.override.yml up -d --build
    echo -e "${GREEN}✓ Development services running${NC}"
    echo -e "${YELLOW}Note: Hot-reload enabled, code changes apply immediately${NC}"
    sleep 2
    cmd_status
}

cmd_prod() {
    echo -e "${YELLOW}▶ Starting in production mode...${NC}"
    if [ ! -f ".env.prod" ]; then
        echo -e "${YELLOW}⚠ Warning: .env.prod not found, using .env${NC}"
    fi
    $DOCKER_COMPOSE_CMD -f $COMPOSE_FILE -f docker-compose.prod.yml up -d --build
    echo -e "${GREEN}✓ Production services running${NC}"
    sleep 3
    cmd_status
}

cmd_push() {
    echo -e "${RED}Push to registry not yet configured${NC}"
    echo "Configure in docker-manage.sh with your registry details"
}

# Main script logic
check_docker

if [ $# -eq 0 ]; then
    print_header
    echo -e "${YELLOW}No command specified${NC}\n"
    print_usage
    exit 1
fi

case "$1" in
    start)           cmd_start ;;
    stop)            cmd_stop ;;
    restart)         cmd_restart ;;
    build)           cmd_build ;;
    up)              cmd_up ;;
    down)            cmd_down ;;
    clean)           cmd_clean ;;
    logs)            shift; cmd_logs "$@" ;;
    logs-backend)    cmd_logs $BACKEND_SERVICE ;;
    logs-streamlit)  cmd_logs $STREAMLIT_SERVICE ;;
    status)          cmd_status ;;
    health)          cmd_health ;;
    shell-backend)   cmd_shell_backend ;;
    shell-streamlit) cmd_shell_streamlit ;;
    test)            cmd_test ;;
    stats)           cmd_stats ;;
    dev)             cmd_dev ;;
    prod)            cmd_prod ;;
    push)            cmd_push ;;
    help|-h)         print_usage ;;
    *)               echo -e "${RED}Unknown command: $1${NC}"; print_usage; exit 1 ;;
esac

exit 0
