#!/bin/bash
# KitchenSage Development Services Stopper
# Cleanly stops both frontend and backend services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${PROJECT_ROOT}/.pids"

BACKEND_PID="${PID_DIR}/backend.pid"
FRONTEND_PID="${PID_DIR}/frontend.pid"

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Kill process by PID
kill_pid() {
    local pid=$1
    local service=$2

    if ! ps -p "$pid" > /dev/null 2>&1; then
        return 1
    fi

    print_message "$BLUE" "🛑 Stopping $service (PID: $pid)..."

    # Try graceful shutdown first
    kill "$pid" 2>/dev/null || true

    # Wait up to 10 seconds for graceful shutdown
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done

    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        print_message "$YELLOW" "⚠️  Forcing $service to stop..."
        kill -9 "$pid" 2>/dev/null || true
        sleep 1
    fi

    # Verify it stopped
    if ps -p "$pid" > /dev/null 2>&1; then
        print_message "$RED" "❌ Failed to stop $service (PID: $pid)"
        return 1
    else
        print_message "$GREEN" "✅ $service stopped successfully"
        return 0
    fi
}

# Stop processes on a specific port
stop_by_port() {
    local port=$1
    local service=$2
    local stopped=false

    # Find all PIDs listening on this port
    local pids=$(lsof -ti :$port 2>/dev/null)

    if [ -z "$pids" ]; then
        return 0
    fi

    for pid in $pids; do
        if kill_pid "$pid" "$service on port $port"; then
            stopped=true
        fi
    done

    if [ "$stopped" = true ]; then
        return 0
    else
        return 1
    fi
}

# Stop a service
stop_service() {
    local service=$1
    local pid_file=$2
    local port=$3

    local stopped=false

    # Try to stop using PID file first
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")

        if ps -p "$pid" > /dev/null 2>&1; then
            if kill_pid "$pid" "$service"; then
                stopped=true
                rm -f "$pid_file"
            fi
        else
            print_message "$YELLOW" "⚠️  $service PID file is stale (PID: $pid)"
            rm -f "$pid_file"
        fi
    else
        print_message "$YELLOW" "⚠️  No PID file for $service"
    fi

    # Also check for orphaned processes on the port
    if [ -n "$port" ]; then
        if stop_by_port "$port" "$service"; then
            stopped=true
        fi
    fi

    if [ "$stopped" = true ]; then
        return 0
    else
        print_message "$YELLOW" "⚠️  $service was not running"
        return 0
    fi
}

# Main execution
main() {
    print_message "$GREEN" "======================================"
    print_message "$GREEN" "  Stopping KitchenSage Services"
    print_message "$GREEN" "======================================"
    echo ""

    stop_service "Backend" "$BACKEND_PID" "8000"
    stop_service "Frontend" "$FRONTEND_PID" "5173"

    # Also check for any orphaned Vite servers on alternate ports
    for port in 5174 5175 5176 5177 5178 5179; do
        if lsof -ti :$port > /dev/null 2>&1; then
            print_message "$YELLOW" "⚠️  Found orphaned process on port $port"
            stop_by_port "$port" "Orphaned Vite server"
        fi
    done

    echo ""
    print_message "$GREEN" "✅ All services stopped"
    echo ""
}

main
