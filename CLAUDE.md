# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KitchenSage is an AI-powered cooking assistant with a React frontend and Python backend powered by CrewAI agents. It provides recipe management, meal planning, recipe discovery, grocery list generation, and a natural language chat interface.

## Project Structure

```
KitchenSage/
├── backend/                 # Python backend (FastAPI + CrewAI)
│   ├── src/
│   │   ├── api/            # FastAPI routes
│   │   ├── services/       # Business logic layer
│   │   ├── agents/         # CrewAI agent definitions
│   │   ├── tasks/          # Task definitions
│   │   ├── tools/          # Agent tools
│   │   ├── models/         # Pydantic models
│   │   ├── database/       # Database repositories
│   │   └── utils/          # Utilities
│   ├── tests/              # Python tests
│   ├── main.py             # CLI entry point
│   └── run_api.py          # API server entry point
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── vite.config.ts
└── docs/                    # Documentation
```

## Managing Services

**IMPORTANT**: Always use the utility scripts in the root directory to manage services:

```bash
# From the root KitchenSage/ directory
./stop.sh                         # Stop all running services (backend + frontend)
                                  # This prevents ghost processes and orphaned ports
```

**DO NOT** use `pkill` or manual process killing - use `./stop.sh` to ensure clean shutdowns and prevent orphaned processes on ports 8000 (backend) and 5173 (frontend).

## Development Commands

### Backend (Python)

```bash
cd backend

# Package Management (use uv exclusively)
uv sync                           # Sync dependencies
uv add <package>                  # Add dependency
uv run python <script>            # Run Python script

# Running the API server
uv run python run_api.py          # Start API at http://localhost:8000
                                  # Docs at http://localhost:8000/docs

# Running the CLI
uv run python main.py chat        # Interactive chat interface
uv run python main.py ask "query" # Single query mode

# Database
uv run python scripts/init_db.py  # Initialize SQLite database

# Testing
uv run pytest                     # Run all tests
uv run pytest tests/test_file.py  # Run specific test
```

### Frontend (React)

```bash
cd frontend

# Dependencies
npm install                       # Install dependencies

# Development
npm run dev                       # Start dev server at http://localhost:5173

# Testing
npm run test                      # Run tests in watch mode
npm run test:run                  # Run tests once
npm run test:coverage             # Run tests with coverage report
npm run test:ui                   # Run tests with UI interface

# Build
npm run build                     # Production build
npm run preview                   # Preview production build
```

## Architecture

### Backend Layers

1. **API Layer** (`src/api/`): FastAPI routes with CORS for frontend
2. **Service Layer** (`src/services/`): Business logic bridging API to agents
3. **Agent Layer** (`src/agents/`): CrewAI agents for AI operations
4. **Database Layer** (`src/database/`): Repository pattern with SQLite

### Flow
```
API Route → Service → Agent/Crew → Tools → Database
```

### Key Agents
- **OrchestratorAgent**: Natural language understanding and routing
- **RecipeManagerAgent**: Database operations and recipe management
- **MealPlannerAgent**: Strategic meal planning
- **RecipeScoutAgent**: Recipe discovery from external sources
- **GroceryListAgent**: Shopping list optimization

### Frontend Stack
- **Vite**: Build tool and dev server
- **React + TypeScript**: UI framework
- **Tailwind CSS**: Utility-first styling
- **React Router**: Client-side routing

## Code Conventions

### Backend (Python)

```python
# Import order
import os, logging                    # Standard library
from pydantic import BaseModel        # Third-party
from src.models.recipe import Recipe  # Local

# Return patterns for services
return {"status": "success", "data": result}
return {"status": "error", "message": str(e)}

# Database operations use context managers
with get_db_connection() as conn:
    # operations
```

### Frontend (TypeScript)

```typescript
// Components use function declarations
export function MyComponent() { ... }

// API calls use the typed api service
import { recipeApi } from '../services/api';
const recipes = await recipeApi.list();

// Tailwind for styling - prefer custom theme colors
className="bg-sage-600 text-cream-100"
```

### Theme Colors (Frontend)
- **Sage**: Primary green (sage-400 to sage-800)
- **Terracotta**: Accent orange (terracotta-400 to terracotta-600)
- **Cream**: Background (cream-50 to cream-300)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recipes` | List recipes with filters |
| GET | `/api/recipes/{id}` | Get recipe by ID |
| POST | `/api/recipes` | Create recipe |
| POST | `/api/recipes/discover` | Discover via AI |
| GET | `/api/meal-plans` | List meal plans |
| POST | `/api/meal-plans` | Create via AI |
| GET | `/api/grocery-lists` | List grocery lists |
| POST | `/api/grocery-lists` | Generate from meal plan |
| POST | `/api/chat` | Chat (SSE streaming) |
| POST | `/api/chat/sync` | Chat (non-streaming) |

## Environment Setup

1. Copy `env_example.txt` to `.env` in project root
2. Configure OpenAI API key
3. Optionally configure Phoenix tracing

## Testing Strategy

### Automated Testing Workflow

**ALWAYS run frontend tests when making frontend changes:**

```bash
cd frontend
npm run test:run  # Run all tests once to check for issues
```

The test suite includes:
- **Rendering Tests**: Verify components render without crashing
- **Console Error Detection**: Catch JavaScript errors and React warnings
- **Router Navigation**: Test that routing works correctly
- **API Mocking**: Prevent real API calls during testing

### When to Run Tests

1. **Before committing frontend changes** - Run `npm run test:run`
2. **During development** - Use `npm run test` for watch mode
3. **For debugging CSS/JS issues** - Tests catch console errors that indicate problems like the Tailwind utility issue

### Test Files

- `src/App.test.tsx` - Main app rendering and routing tests
- `src/test/console-errors.test.tsx` - Console error detection
- `src/test/setup.ts` - Test configuration and console monitoring
- `src/test/test-utils.tsx` - Custom render helpers with providers

## Important Notes

- Use `uv` for Python package management, not pip
- Backend imports use `from src.xxx` pattern
- Frontend proxies `/api` to backend in development
- All LLM-dependent code is in `agents/` and `tasks/` for easy framework swaps
- Chat uses Server-Sent Events for real-time streaming
- **Run frontend tests before committing** to catch rendering and console errors
