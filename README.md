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

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/KitchenSage.git
   cd KitchenSage
   ```

2. Create environment file:
   ```bash
   cp env_example.txt .env
   # Edit .env and add your OpenAI API key
   ```

### Running the Backend

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

## Development

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest

# With verbose output
uv run pytest -v
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

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI agents | Yes |
| `PHOENIX_API_KEY` | Phoenix tracing key | No |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
