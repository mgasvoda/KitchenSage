#!/bin/bash
# KitchenSage Log Viewer
# View logs from frontend and/or backend services

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"

BACKEND_LOG="${LOG_DIR}/backend.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Show usage
show_usage() {
    echo "Usage: ./logs.sh [backend|frontend|both|errors] [--follow|-f] [--lines N]"
    echo ""
    echo "Options:"
    echo "  backend           View backend logs only"
    echo "  frontend          View frontend logs only"
    echo "  both              View both logs (default)"
    echo "  errors            View only errors from both services"
    echo "  --follow, -f      Follow logs (tail -f)"
    echo "  --lines N         Show last N lines (default: 50)"
    echo ""
    echo "Examples:"
    echo "  ./logs.sh backend            # Show last 50 lines of backend logs"
    echo "  ./logs.sh frontend -f        # Follow frontend logs"
    echo "  ./logs.sh both --lines 100   # Show last 100 lines of both"
    echo "  ./logs.sh errors             # Show only errors"
}

# View backend logs
view_backend() {
    local follow=$1
    local lines=$2

    if [ ! -f "$BACKEND_LOG" ]; then
        print_message "$YELLOW" "⚠️  Backend log file not found: $BACKEND_LOG"
        return 1
    fi

    print_message "$BLUE" "======================================"
    print_message "$BLUE" "  Backend Logs"
    print_message "$BLUE" "======================================"
    echo ""

    if [ "$follow" = "true" ]; then
        tail -f "$BACKEND_LOG"
    else
        tail -n "$lines" "$BACKEND_LOG"
    fi
}

# View frontend logs
view_frontend() {
    local follow=$1
    local lines=$2

    if [ ! -f "$FRONTEND_LOG" ]; then
        print_message "$YELLOW" "⚠️  Frontend log file not found: $FRONTEND_LOG"
        return 1
    fi

    print_message "$GREEN" "======================================"
    print_message "$GREEN" "  Frontend Logs"
    print_message "$GREEN" "======================================"
    echo ""

    if [ "$follow" = "true" ]; then
        tail -f "$FRONTEND_LOG"
    else
        tail -n "$lines" "$FRONTEND_LOG"
    fi
}

# View both logs
view_both() {
    local follow=$1
    local lines=$2

    if [ "$follow" = "true" ]; then
        print_message "$CYAN" "Following both backend and frontend logs (Ctrl+C to stop)..."
        echo ""
        tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
    else
        view_backend false "$lines"
        echo ""
        view_frontend false "$lines"
    fi
}

# View only errors
view_errors() {
    local lines=$1

    print_message "$RED" "======================================"
    print_message "$RED" "  Error Logs"
    print_message "$RED" "======================================"
    echo ""

    print_message "$BLUE" "Backend Errors:"
    if [ -f "$BACKEND_LOG" ]; then
        grep -i -E "(error|exception|traceback|failed)" "$BACKEND_LOG" | tail -n "$lines" || print_message "$GREEN" "No errors found"
    else
        print_message "$YELLOW" "Log file not found"
    fi

    echo ""
    print_message "$GREEN" "Frontend Errors:"
    if [ -f "$FRONTEND_LOG" ]; then
        grep -i -E "(error|exception|failed|✘)" "$FRONTEND_LOG" | tail -n "$lines" || print_message "$GREEN" "No errors found"
    else
        print_message "$YELLOW" "Log file not found"
    fi
}

# Main execution
main() {
    local service="both"
    local follow=false
    local lines=50

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            backend|frontend|both|errors)
                service=$1
                shift
                ;;
            --follow|-f)
                follow=true
                shift
                ;;
            --lines)
                lines=$2
                shift 2
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                print_message "$RED" "Unknown option: $1"
                echo ""
                show_usage
                exit 1
                ;;
        esac
    done

    # View logs based on service selection
    case $service in
        backend)
            view_backend "$follow" "$lines"
            ;;
        frontend)
            view_frontend "$follow" "$lines"
            ;;
        both)
            view_both "$follow" "$lines"
            ;;
        errors)
            view_errors "$lines"
            ;;
    esac
}

main "$@"
