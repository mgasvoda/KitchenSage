#!/bin/bash
# KitchenSage Service Status Checker
# Check the status of frontend and backend services

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

# Check service status
check_service() {
    local service=$1
    local pid_file=$2
    local port=$3
    local url=$4

    echo ""
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_message "$BLUE" "  $service Service"
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Check PID file
    if [ ! -f "$pid_file" ]; then
        print_message "$RED" "Status: ❌ Not Running"
        print_message "$YELLOW" "PID File: Not found"
        return 1
    fi

    local pid=$(cat "$pid_file")

    # Check if process is running
    if ! ps -p "$pid" > /dev/null 2>&1; then
        print_message "$RED" "Status: ❌ Not Running (stale PID)"
        print_message "$YELLOW" "PID File: $pid_file (stale)"
        return 1
    fi

    print_message "$GREEN" "Status: ✅ Running"
    print_message "$GREEN" "PID: $pid"

    # Get process info
    local process_info=$(ps -p "$pid" -o etime= -o rss= 2>/dev/null || echo "unknown unknown")
    local uptime=$(echo "$process_info" | awk '{print $1}')
    local memory=$(echo "$process_info" | awk '{print $2}')

    if [ "$uptime" != "unknown" ]; then
        print_message "$BLUE" "Uptime: $uptime"
        # Convert KB to MB
        memory_mb=$((memory / 1024))
        print_message "$BLUE" "Memory: ${memory_mb}MB"
    fi

    # Check if port is listening
    if command -v lsof > /dev/null 2>&1; then
        if lsof -i ":$port" -sTCP:LISTEN > /dev/null 2>&1; then
            print_message "$GREEN" "Port: $port (listening)"
        else
            print_message "$YELLOW" "Port: $port (not listening)"
        fi
    elif command -v netstat > /dev/null 2>&1; then
        if netstat -tuln | grep ":$port " > /dev/null 2>&1; then
            print_message "$GREEN" "Port: $port (listening)"
        else
            print_message "$YELLOW" "Port: $port (not listening)"
        fi
    fi

    # Check HTTP endpoint
    if [ -n "$url" ]; then
        if curl -s "$url" > /dev/null 2>&1; then
            print_message "$GREEN" "Health: ✅ Responding"
            print_message "$BLUE" "URL: $url"
        else
            print_message "$YELLOW" "Health: ⚠️  Not responding"
            print_message "$YELLOW" "URL: $url (check not available)"
        fi
    fi

    return 0
}

# Show recent errors
show_recent_errors() {
    local service=$1
    local log_file=$2

    if [ ! -f "$log_file" ]; then
        return
    fi

    local error_count=$(grep -i -c -E "(error|exception|failed)" "$log_file" 2>/dev/null || echo "0")

    if [ "$error_count" -gt 0 ]; then
        print_message "$RED" "Recent Errors: $error_count found"
        print_message "$YELLOW" "Last error:"
        grep -i -E "(error|exception|failed)" "$log_file" | tail -n 1
    else
        print_message "$GREEN" "Recent Errors: None"
    fi
}

# Main execution
main() {
    print_message "$GREEN" "╔════════════════════════════════════╗"
    print_message "$GREEN" "║  KitchenSage Service Status        ║"
    print_message "$GREEN" "╚════════════════════════════════════╝"

    local backend_status=1
    local frontend_status=1

    # Check backend
    check_service "Backend" "$BACKEND_PID" "8000" "http://localhost:8000/docs"
    backend_status=$?
    if [ $backend_status -eq 0 ]; then
        show_recent_errors "Backend" "$BACKEND_LOG"
    fi

    # Check frontend
    check_service "Frontend" "$FRONTEND_PID" "5173" "http://localhost:5173"
    frontend_status=$?
    if [ $frontend_status -eq 0 ]; then
        show_recent_errors "Frontend" "$FRONTEND_LOG"
    fi

    echo ""
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_message "$BLUE" "  Summary"
    print_message "$BLUE" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ $backend_status -eq 0 ] && [ $frontend_status -eq 0 ]; then
        print_message "$GREEN" "All services: ✅ Running"
    elif [ $backend_status -eq 0 ] || [ $frontend_status -eq 0 ]; then
        print_message "$YELLOW" "Some services: ⚠️  Running (partial)"
    else
        print_message "$RED" "All services: ❌ Stopped"
    fi

    echo ""
    print_message "$BLUE" "Commands:"
    print_message "$BLUE" "  Start:  ./start.sh"
    print_message "$BLUE" "  Stop:   ./stop.sh"
    print_message "$BLUE" "  Logs:   ./logs.sh [backend|frontend|both]"
    echo ""
}

main
