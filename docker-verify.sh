#!/bin/bash
# docker-verify.sh
# Pre-deployment verification script for PHOENIX Radar AI
# Checks system requirements and Docker setup before deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  PHOENIX Radar AI - Docker Deployment Verification       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check functions
check_docker_installed() {
    echo -n "Checking Docker installation... "
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  → Install Docker from https://docs.docker.com/install/"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_docker_version() {
    echo -n "Checking Docker version (>= 20.10.0)... "
    VERSION=$(docker --version | grep -oP 'Docker version \K[^,]+' || echo "0.0.0")
    IFS='.' read -ra PARTS <<< "$VERSION"
    if (( PARTS[0] > 20 || (PARTS[0] == 20 && PARTS[1] >= 10) )); then
        echo -e "${GREEN}✓${NC} (${VERSION})"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} (${VERSION})"
        echo "  → Recommended: Docker 20.10.0 or later"
        ((CHECKS_WARNED++))
        return 0
    fi
}

check_docker_daemon() {
    echo -n "Checking Docker daemon status... "
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  → Start Docker daemon: sudo systemctl start docker (Linux) or open Docker Desktop (Mac/Win)"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_docker_compose() {
    echo -n "Checking Docker Compose installation... "
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  → Install Docker Compose: docker-compose plugin or standalone"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_compose_version() {
    echo -n "Checking Docker Compose version (>= 2.0)... "
    VERSION=$(docker compose version | grep -oP 'v\K[^,]+' || echo "0.0.0")
    IFS='.' read -ra PARTS <<< "$VERSION"
    if (( PARTS[0] >= 2 )); then
        echo -e "${GREEN}✓${NC} (${VERSION})"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} (${VERSION})"
        echo "  → Recommended: Docker Compose 2.0+ (docker compose, not docker-compose)"
        ((CHECKS_WARNED++))
        return 0
    fi
}

check_disk_space() {
    echo -n "Checking available disk space (>= 2 GB)... "
    AVAILABLE=$(df /home | awk 'NR==2 {print $4}')
    if (( AVAILABLE > 2097152 )); then  # 2 GB in KB
        AVAILABLE_GB=$((AVAILABLE / 1048576))
        echo -e "${GREEN}✓${NC} (${AVAILABLE_GB} GB available)"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} ($(($AVAILABLE / 1048576)) GB available)"
        echo "  → Need at least 2 GB for images and containers"
        ((CHECKS_WARNED++))
        return 0
    fi
}

check_ports_available() {
    echo -n "Checking ports (8000, 8501) availability... "
    PORT8000=$(netstat -tuln 2>/dev/null | grep :8000 || echo "")
    PORT8501=$(netstat -tuln 2>/dev/null | grep :8501 || echo "")
    
    if [ -z "$PORT8000" ] && [ -z "$PORT8501" ]; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        PORTS_BUSY=""
        [ -n "$PORT8000" ] && PORTS_BUSY="8000"
        [ -n "$PORT8501" ] && PORTS_BUSY="$PORTS_BUSY 8501"
        echo -e "${YELLOW}⚠${NC} (${PORTS_BUSY} already in use)"
        echo "  → Free ports or use different ones in .env"
        ((CHECKS_WARNED++))
        return 0
    fi
}

check_deployment_files() {
    echo -n "Checking Docker deployment files... "
    FILES=("Dockerfile" "docker-compose.yml" ".dockerignore" ".env.example")
    MISSING=()
    for file in "${FILES[@]}"; do
        [ ! -f "$file" ] && MISSING+=("$file")
    done
    
    if [ ${#MISSING[@]} -eq 0 ]; then
        echo -e "${GREEN}✓${NC} (4/4 present)"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        echo "  → Missing: ${MISSING[*]}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

check_docker_socket() {
    echo -n "Checking Docker socket access... "
    if [ -S /var/run/docker.sock ] && docker ps &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC}"
        echo "  → May need to add user to docker group: sudo usermod -aG docker \$USER"
        ((CHECKS_WARNED++))
        return 0
    fi
}

check_git() {
    echo -n "Checking Git installation (optional)... "
    if command -v git &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC}"
        echo "  → Optional but useful for version control"
        ((CHECKS_WARNED++))
        return 0
    fi
}

check_internet() {
    echo -n "Checking internet connectivity... "
    if timeout 2 curl -s https://www.google.com > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC}"
        echo "  → Required to download base images (python:3.11-slim)"
        ((CHECKS_WARNED++))
        return 0
    fi
}

# System info display
show_system_info() {
    echo ""
    echo -e "${BLUE}System Information:${NC}"
    echo "  OS: $(uname -s)"
    echo "  Kernel: $(uname -r)"
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "  Distribution: $PRETTY_NAME"
    fi
    echo ""
}

# Run all checks
run_checks() {
    echo -e "${BLUE}Running Pre-Deployment Checks:${NC}"
    echo ""
    
    check_docker_installed
    check_docker_version
    check_docker_daemon
    check_docker_compose
    check_compose_version
    check_disk_space
    check_ports_available
    check_deployment_files
    check_docker_socket
    check_git
    check_internet
}

# Show results
show_results() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Verification Results:${NC}"
    echo -e "${GREEN}✓ Passed:${NC}  $CHECKS_PASSED"
    echo -e "${RED}✗ Failed:${NC}  $CHECKS_FAILED"
    echo -e "${YELLOW}⚠ Warned:${NC}  $CHECKS_WARNED"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Deployment readiness
show_readiness() {
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}🚀 System Ready for Deployment!${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. cp .env.example .env"
        echo "  2. docker compose up --build"
        echo "  3. Open http://localhost:8501"
        echo ""
        return 0
    else
        echo -e "${RED}❌ System Not Ready${NC}"
        echo ""
        echo "Please fix the above errors before deploying."
        echo ""
        return 1
    fi
}

# Help text
show_help() {
    cat << 'EOF'
This script verifies your Docker setup before deploying PHOENIX Radar AI.

It checks:
  ✓ Docker installation and version
  ✓ Docker daemon running  
  ✓ Docker Compose installation and version
  ✓ Available disk space (>= 2 GB)
  ✓ Port availability (8000, 8501)
  ✓ Deployment files present
  ✓ Docker socket access
  ✓ Optional: Git, Internet connectivity

Results:
  Green (✓)   = Ready
  Red (✗)     = Error - must fix before deployment
  Yellow (⚠)  = Warning - deployment may work but verify

Usage:
  ./docker-verify.sh       # Run full verification
  ./docker-verify.sh -h    # Show this help
  ./docker-verify.sh -info # Show system info only
EOF
}

# Main logic
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -info|--info)
            show_system_info
            exit 0
            ;;
        *)
            show_system_info
            run_checks
            show_results
            show_readiness
            ;;
    esac
}

main "$@"
