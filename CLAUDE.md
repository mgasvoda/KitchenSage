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
4. Optionally tune LLM and application settings (see Configuration below)

## Configuration

### Settings Architecture

KitchenSage uses a centralized configuration system located in `backend/src/config/settings.py`. Settings are managed using Pydantic and can be overridden via environment variables.

### Configurable Settings

#### LLM Models
Control which OpenAI models are used for different agents:
- `LLM_DEFAULT_MODEL` - Default model for general tasks (default: `gpt-4o-mini`)
- `LLM_CONSOLIDATION_MODEL` - Model for grocery list consolidation (default: `gpt-4o-mini`)
- `LLM_ORCHESTRATOR_MODEL` - Model for orchestrator agent (default: `gpt-4.1-mini`)
- `LLM_MEAL_PLANNER_MODEL` - Model for meal planning (default: `gpt-4.1-mini`)
- `LLM_RECIPE_SCOUT_MODEL` - Model for recipe discovery (default: `gpt-4.1-mini`)
- `LLM_RECIPE_MANAGER_MODEL` - Model for recipe management (default: `gpt-4.1-mini`)
- `LLM_GROCERY_LIST_MODEL` - Model for grocery list agent (default: `gpt-4.1-mini`)

#### LLM Behavior
Control LLM temperature and token usage:
- `LLM_ORCHESTRATOR_TEMPERATURE` - Temperature for orchestrator (default: `0.1`)
- `LLM_MEAL_PLANNER_TEMPERATURE` - Temperature for meal planner (default: `0.3`)
- `LLM_RECIPE_SCOUT_TEMPERATURE` - Temperature for recipe scout (default: `0.4`)
- `LLM_RECIPE_MANAGER_TEMPERATURE` - Temperature for recipe manager (default: `0.1`)
- `LLM_GROCERY_LIST_TEMPERATURE` - Temperature for grocery list (default: `0.2`)
- `LLM_CONSOLIDATION_TEMPERATURE` - Temperature for consolidation (default: `0.1`)
- `LLM_CONSOLIDATION_MAX_TOKENS` - Max tokens for consolidation (default: `4000`)
- `LLM_AGENT_VERBOSE` - Enable verbose agent output (default: `true`)

#### Meal Planning Defaults
Default values for meal plan generation:
- `MEAL_DEFAULT_DAYS` - Default number of days (default: `7`)
- `MEAL_DEFAULT_PEOPLE` - Default number of people (default: `2`)
- `MEAL_DEFAULT_SERVINGS` - Default servings when not specified (default: `4`)
- `MEAL_MEALS_PER_DAY` - Number of meals per day (default: `3`)

#### Recipe Discovery
Settings for recipe search and discovery:
- `RECIPE_DEFAULT_MAX_RESULTS` - Max recipes to discover (default: `5`)
- `RECIPE_DEFAULT_SERVINGS_FALLBACK` - Fallback when scraping fails (default: `4`)

### Accessing Settings in Code

```python
from src.config import settings

# Access LLM settings
model = settings.llm.orchestrator_model
temp = settings.llm.orchestrator_temperature

# Access meal planning defaults
days = settings.meal_planning.default_days
people = settings.meal_planning.default_people
```

All settings have sensible defaults and are optional - the application works out of the box without any environment variable configuration beyond the required OpenAI API key.

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
