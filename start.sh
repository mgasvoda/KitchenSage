#!/bin/bash
# KitchenSage Development Services Starter
# Starts both frontend and backend services with logging to files

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_DIR="${PROJECT_ROOT}/.pids"

# Create necessary directories
mkdir -p "${LOG_DIR}"
mkdir -p "${PID_DIR}"

# Log files
BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"
BACKEND_PID="${PID_DIR}/backend.pid"
FRONTEND_PID="${PID_DIR}/frontend.pid"

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if a service is already running
check_running() {
    local service=$1
    local pid_file=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_message "$YELLOW" "⚠️  $service is already running (PID: $pid)"
            return 0
        else
            # Stale PID file
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Start backend service
start_backend() {
    print_message "$BLUE" "🚀 Starting backend service..."

    if check_running "Backend" "$BACKEND_PID"; then
        return 0
    fi

    cd "${PROJECT_ROOT}/backend"

    # Clear old log
    > "$BACKEND_LOG"

    # Start backend with uv
    nohup uv run python run_api.py > "$BACKEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$BACKEND_PID"

    # Wait a moment and check if it started
    sleep 2
    if ps -p $pid > /dev/null 2>&1; then
        print_message "$GREEN" "✅ Backend started successfully (PID: $pid)"
        print_message "$BLUE" "   API: http://localhost:8000"
        print_message "$BLUE" "   Docs: http://localhost:8000/docs"
        print_message "$BLUE" "   Logs: $BACKEND_LOG"
    else
        print_message "$RED" "❌ Backend failed to start. Check logs:"
        tail -n 20 "$BACKEND_LOG"
        rm -f "$BACKEND_PID"
        return 1
    fi
}

# Start frontend service
start_frontend() {
    print_message "$BLUE" "🚀 Starting frontend service..."

    if check_running "Frontend" "$FRONTEND_PID"; then
        return 0
    fi

    cd "${PROJECT_ROOT}/frontend"

    # Clear old log
    > "$FRONTEND_LOG"

    # Start frontend with npm
    nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
    local pid=$!
    echo $pid > "$FRONTEND_PID"

    # Wait a moment and check if it started
    sleep 3
    if ps -p $pid > /dev/null 2>&1; then
        print_message "$GREEN" "✅ Frontend started successfully (PID: $pid)"
        print_message "$BLUE" "   URL: http://localhost:5173"
        print_message "$BLUE" "   Logs: $FRONTEND_LOG"
    else
        print_message "$RED" "❌ Frontend failed to start. Check logs:"
        tail -n 20 "$FRONTEND_LOG"
        rm -f "$FRONTEND_PID"
        return 1
    fi
}

# Check service health
check_health() {
    local service=$1
    local url=$2
    local max_attempts=10
    local attempt=0

    print_message "$BLUE" "🏥 Checking $service health..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_message "$GREEN" "✅ $service is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    print_message "$YELLOW" "⚠️  $service health check timed out"
    return 1
}

# Main execution
main() {
    print_message "$GREEN" "======================================"
    print_message "$GREEN" "  KitchenSage Development Services"
    print_message "$GREEN" "======================================"
    echo ""

    # Start services
    start_backend
    start_frontend

    echo ""
    print_message "$GREEN" "======================================"
    print_message "$GREEN" "  Service Status"
    print_message "$GREEN" "======================================"
    echo ""

    # Check health
    check_health "Backend API" "http://localhost:8000/docs"
    check_health "Frontend" "http://localhost:5173"

    echo ""
    print_message "$GREEN" "======================================"
    print_message "$GREEN" "  Quick Commands"
    print_message "$GREEN" "======================================"
    echo ""
    print_message "$BLUE" "  View logs:        ./logs.sh [backend|frontend|both]"
    print_message "$BLUE" "  Stop services:    ./stop.sh"
    print_message "$BLUE" "  Service status:   ./status.sh"
    echo ""
    print_message "$BLUE" "  Logs directory:   $LOG_DIR"
    print_message "$BLUE" "  PIDs directory:   $PID_DIR"
    echo ""
    print_message "$GREEN" "🎉 All services are running!"
    echo ""
}

main
