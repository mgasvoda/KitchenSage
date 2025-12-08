# KitchenSage Service Management

This directory contains utility scripts for managing the KitchenSage development environment. These scripts handle starting, stopping, and monitoring both the frontend and backend services.

## Quick Start

```bash
# Start all services
./start.sh

# Check service status
./status.sh

# View logs
./logs.sh

# Stop all services
./stop.sh
```

## Scripts Overview

### `start.sh` - Start Services

Starts both frontend and backend services in the background with logging.

```bash
./start.sh
```

**Features:**
- Starts backend API server (FastAPI on port 8000)
- Starts frontend dev server (Vite on port 5173)
- Performs health checks on both services
- Creates PID files for process management
- Logs output to `logs/backend.log` and `logs/frontend.log`
- Prevents duplicate starts (checks if already running)

**Output:**
- Backend API: http://localhost:8000
- Backend Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173

### `stop.sh` - Stop Services

Gracefully stops all running services.

```bash
./stop.sh
```

**Features:**
- Graceful shutdown with SIGTERM first
- Force kill (SIGKILL) after 10 seconds if needed
- Cleans up PID files
- Verifies services stopped successfully

### `status.sh` - Check Service Status

Displays detailed status information for all services.

```bash
./status.sh
```

**Shows:**
- Running status (PID, uptime, memory usage)
- Port listening status
- HTTP health check results
- Recent error count from logs
- Summary of all services

**Example Output:**
```
╔════════════════════════════════════╗
║  KitchenSage Service Status        ║
╚════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Backend Service
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: ✅ Running
PID: 12345
Uptime: 01:23
Memory: 58MB
Port: 8000 (listening)
Health: ✅ Responding
URL: http://localhost:8000/docs
Recent Errors: None
```

### `logs.sh` - View Service Logs

View logs from backend and/or frontend services.

```bash
# View backend logs (last 50 lines)
./logs.sh backend

# View frontend logs (last 50 lines)
./logs.sh frontend

# View both logs (last 50 lines each)
./logs.sh both

# View only errors from both services
./logs.sh errors

# Follow logs in real-time (like tail -f)
./logs.sh backend --follow
./logs.sh frontend -f

# Show last 100 lines
./logs.sh both --lines 100

# Follow both logs
./logs.sh both -f
```

**Options:**
- `backend` - View backend logs only
- `frontend` - View frontend logs only
- `both` - View both logs (default)
- `errors` - View only error lines from both services
- `--follow, -f` - Follow logs in real-time
- `--lines N` - Show last N lines (default: 50)

## File Locations

### Logs Directory: `logs/`
- `backend.log` - Backend API server logs
- `frontend.log` - Frontend dev server logs

### PIDs Directory: `.pids/`
- `backend.pid` - Backend process ID
- `frontend.pid` - Frontend process ID

## Common Workflows

### Starting Development

```bash
# Start all services
./start.sh

# Verify everything is running
./status.sh

# Follow logs to watch for issues
./logs.sh both -f
```

### Debugging Issues

```bash
# Check if services are running
./status.sh

# View recent errors
./logs.sh errors

# View detailed backend logs
./logs.sh backend --lines 100

# Follow frontend logs in real-time
./logs.sh frontend -f
```

### Stopping Work

```bash
# Stop all services
./stop.sh

# Verify they stopped
./status.sh
```

### Restarting Services

```bash
# Stop all services
./stop.sh

# Start them again
./start.sh
```

Or restart a specific service:

```bash
# Stop all
./stop.sh

# Start just to see startup logs
./start.sh

# If there's an issue, check logs
./logs.sh backend
```

## Service Details

### Backend Service

- **Technology:** Python FastAPI with uvicorn
- **Port:** 8000
- **Command:** `uv run python backend/run_api.py`
- **Health Check:** http://localhost:8000/docs
- **Features:**
  - Hot reload enabled
  - API documentation at `/docs`
  - CORS enabled for frontend

### Frontend Service

- **Technology:** Vite + React
- **Port:** 5173
- **Command:** `npm run dev` (in frontend directory)
- **URL:** http://localhost:5173
- **Features:**
  - Hot module replacement (HMR)
  - Proxies `/api` to backend
  - Fast refresh for React

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are already in use
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# View full logs for errors
./logs.sh backend
./logs.sh frontend
```

### Services Keep Crashing

```bash
# Check logs for errors
./logs.sh errors

# Follow logs to see crash details
./logs.sh backend -f
```

### Can't Stop Services

```bash
# Force stop using PIDs directly
cat .pids/backend.pid | xargs kill -9
cat .pids/frontend.pid | xargs kill -9

# Clean up PID files
rm -f .pids/*.pid
```

### Stale PID Files

If you see warnings about stale PIDs, the scripts will automatically clean them up. You can also manually remove them:

```bash
rm -f .pids/*.pid
```

## Advanced Usage

### Running Specific Service

You can modify `start.sh` or start services manually:

```bash
# Start only backend
cd backend && uv run python run_api.py

# Start only frontend
cd frontend && npm run dev
```

### Custom Ports

To change default ports, edit:
- Backend: `backend/run_api.py` (line 30, port parameter)
- Frontend: `frontend/vite.config.ts` (line 12, server.port)

### Log Rotation

Logs are overwritten each time you run `./start.sh`. To preserve old logs:

```bash
# Before starting, backup logs
cp logs/backend.log logs/backend.log.old
cp logs/frontend.log logs/frontend.log.old

# Then start
./start.sh
```

## Requirements

- **Backend:** Python 3.x, uv package manager
- **Frontend:** Node.js, npm
- **System:** bash, curl (for health checks)

## Notes

- All scripts must be run from the project root directory
- Services run in the background (daemonized)
- Logs are written to files, not stdout
- PID files track running processes
- Health checks verify services are responding
- Graceful shutdown is attempted before force kill
