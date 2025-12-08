# KitchenSage 🍳

An AI-powered cooking assistant with a modern React frontend and Python backend powered by CrewAI agents. Get recipe recommendations, plan your meals, and generate grocery lists through natural language conversation.

## Features

- **AI Chat Interface**: Conversational cooking assistant with real-time streaming responses
- **Recipe Management**: Browse, search, and manage your recipe collection
- **Meal Planning**: Create weekly meal plans optimized for nutrition and variety
- **Grocery Lists**: Auto-generate shopping lists from your meal plans
- **Multi-Agent System**: Specialized AI agents for different cooking tasks

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS
- React Router

### Backend
- FastAPI (API framework)
- CrewAI (multi-agent orchestration)
- SQLite (database)
- Pydantic (data validation)

## Project Structure

```
KitchenSage/
├── backend/                    # Python backend
│   ├── src/
│   │   ├── api/               # FastAPI routes
│   │   ├── services/          # Business logic layer
│   │   ├── agents/            # CrewAI agents
│   │   ├── tasks/             # Agent tasks
│   │   ├── tools/             # Agent tools
│   │   ├── models/            # Pydantic models
│   │   └── database/          # Database repositories
│   ├── tests/                 # Python tests
│   ├── main.py                # CLI entry point
│   └── run_api.py             # API server entry point
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript types
│   └── package.json
└── docs/                       # Documentation
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- OpenAI API key (required)

### Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/KitchenSage.git
   cd KitchenSage
   ```

2. Create and configure environment file:
   ```bash
   cp env_example.txt .env
   ```

3. **Required:** Edit `.env` and add your OpenAI API key:
   ```bash
   OPENAI_API_KEY=your_actual_api_key_here
   ```

   This is the **only required** environment variable. The application will not function without a valid OpenAI API key.

4. **Optional:** Configure additional settings in `.env`:
   - `PHOENIX_API_KEY` - For Phoenix telemetry/tracing (optional)
   - `LOG_LEVEL` - Logging level (defaults to INFO)
   - `DATABASE_URL` - Database path (defaults to sqlite:///kitchen_crew.db)
   - Other settings are pre-configured with sensible defaults

5. Install dependencies and initialize database:
   ```bash
   # Backend dependencies
   cd backend
   uv sync
   uv run python scripts/init_db.py
   cd ..

   # Frontend dependencies
   cd frontend
   npm install
   cd ..
   ```

6. Start all services:
   ```bash
   ./start.sh
   ```

   This starts both the backend API (http://localhost:8000) and frontend (http://localhost:5173) in the background.

7. Check status, view logs, or stop services:
   ```bash
   ./status.sh              # Check service status
   ./logs.sh both           # View logs
   ./logs.sh errors         # View only errors
   ./stop.sh                # Stop all services
   ```

   See [SERVICES.md](SERVICES.md) for complete service management documentation.

### Manual Setup (Alternative to Quick Start)

If you prefer to run services manually instead of using the management scripts:

#### Running the Backend

```bash
cd backend

# Install dependencies
uv sync

# Initialize the database
uv run python scripts/init_db.py

# Start the API server (http://localhost:8000)
uv run python run_api.py
```

API documentation is available at http://localhost:8000/docs

### Running the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server (http://localhost:5173)
npm run dev
```

### Running the CLI

For a terminal-based chat interface:

```bash
cd backend
uv run python main.py chat
```

### Importing Recipes from Paprika

If you have recipes in the Paprika app, you can import them:

```bash
cd backend
uv run python scripts/import_paprika.py ~/Downloads/Export*.paprikarecipes --dry-run
uv run python scripts/import_paprika.py ~/Downloads/Export*.paprikarecipes
```

See [docs/paprika-import.md](docs/paprika-import.md) for detailed import documentation.

## Development

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest
uv run pytest -v  # With verbose output

# Frontend tests
cd frontend
npm run test:run      # Run all tests once
npm run test          # Run tests in watch mode
npm run test:coverage # Run with coverage report

# E2E tests (Playwright)
cd frontend
npx playwright test              # Run all e2e tests
npx playwright test --ui         # Run with UI mode
npx playwright test --headed     # Run with visible browser
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recipes` | List recipes |
| GET | `/api/recipes/{id}` | Get recipe |
| POST | `/api/recipes` | Create recipe |
| POST | `/api/recipes/discover` | Discover via AI |
| GET | `/api/meal-plans` | List meal plans |
| POST | `/api/meal-plans` | Create via AI |
| GET | `/api/grocery-lists` | List grocery lists |
| POST | `/api/grocery-lists` | Generate from meal plan |
| POST | `/api/chat` | Chat (streaming) |
| POST | `/api/chat/sync` | Chat (non-streaming) |

## Architecture

The system uses a layered architecture:

```
Frontend (React) 
    ↓ HTTP/SSE
API Layer (FastAPI)
    ↓
Service Layer (Business Logic)
    ↓
Agent Layer (CrewAI)
    ↓
Database Layer (SQLite)
```

### AI Agents

- **Orchestrator**: Natural language understanding and routing
- **Recipe Manager**: Database operations and recipe management
- **Meal Planner**: Strategic meal planning
- **Recipe Scout**: External recipe discovery
- **Grocery List Agent**: Shopping list optimization

## Configuration

### Environment Variables

All environment variables are configured in the `.env` file in the project root. See `env_example.txt` for the complete template.

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI agents | **Yes** | None |
| `PHOENIX_API_KEY` | Phoenix telemetry/tracing API key | No | None (skips tracing) |
| `DATABASE_URL` | Database connection string | No | `sqlite:///kitchen_crew.db` |
| `LOG_LEVEL` | Logging verbosity level | No | `INFO` |
| `HOST` | API server host | No | `localhost` |
| `PORT` | API server port | No | `8000` |

**Note:** The application uses only the OpenAI API for all AI operations. The `SPOONACULAR_API_KEY` and `EDAMAM_API_KEY` variables in `env_example.txt` are placeholders for future recipe API integrations but are not currently used by the application.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
