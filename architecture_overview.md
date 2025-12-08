# KitchenSage Architecture Overview

## System Overview

KitchenSage is a full-stack AI-powered cooking assistant featuring a React frontend and Python backend powered by CrewAI agents. The system provides recipe management, meal planning, grocery list generation, and natural language chat interaction.

## Project Structure

```
KitchenSage/
├── backend/                    # Python backend
│   ├── src/
│   │   ├── api/               # FastAPI routes and endpoints
│   │   │   ├── routes/        # Route modules (recipes, meal_plans, grocery, chat)
│   │   │   └── main.py        # FastAPI app setup, CORS, middleware
│   │   ├── services/          # Business logic layer
│   │   │   ├── recipe_service.py
│   │   │   ├── meal_plan_service.py
│   │   │   ├── grocery_service.py
│   │   │   └── chat_service.py
│   │   ├── agents/            # CrewAI agent definitions
│   │   ├── tasks/             # Agent task definitions
│   │   ├── tools/             # Agent tools
│   │   ├── models/            # Pydantic data models
│   │   ├── database/          # Database operations and repositories
│   │   └── utils/             # Utility functions
│   ├── tests/                 # Python tests
│   ├── scripts/               # Utility scripts
│   ├── pyproject.toml
│   ├── main.py               # CLI entry point
│   └── run_api.py            # API server entry point
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── layout/        # Layout components (Sidebar, etc.)
│   │   │   ├── chat/          # Chat-related components
│   │   │   ├── recipes/       # Recipe components
│   │   │   ├── grocery/       # Grocery list components
│   │   │   └── calendar/      # Calendar/meal plan components
│   │   ├── pages/             # Page-level components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript type definitions
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── docs/                       # Documentation
└── README.md
```

## Architecture Layers

### Frontend Layer (React + TypeScript)

- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Tailwind CSS**: Utility-first styling
- **API Client**: Type-safe fetch wrapper with streaming support

### API Layer (FastAPI)

- **Routes**: HTTP endpoints organized by domain
- **CORS**: Configured for frontend development
- **SSE Streaming**: Real-time chat responses
- **OpenAPI**: Auto-generated API documentation

### Service Layer

The service layer acts as a bridge between the API and agents:

```
API Route → Service → Agent/Crew → Tools → Database
```

Services handle:
- Request validation beyond Pydantic
- Coordinating multiple agent calls
- Transforming agent output for API response
- Streaming orchestration for chat

### Agent Layer (CrewAI)

#### Recipe Manager Agent
- **Role**: Database operations and recipe management
- **Goal**: Efficiently store, retrieve, and organize recipe data
- **Tools**: DatabaseTool, RecipeValidatorTool, RecipeSearchTool

#### Meal Planner Agent
- **Role**: Strategic meal planning and nutritional balance
- **Goal**: Create optimal meal plans based on constraints
- **Tools**: MealPlanningTool, NutritionAnalysisTool, CalendarTool

#### Recipe Scout Agent
- **Role**: Discovery and acquisition of new recipes
- **Goal**: Find relevant recipes from various sources
- **Tools**: WebScrapingTool, RecipeAPITool, ContentFilterTool

#### Grocery List Agent
- **Role**: Inventory management and shopping list optimization
- **Goal**: Generate efficient grocery lists with cost optimization
- **Tools**: InventoryTool, PriceComparisonTool, ListOptimizationTool

#### Orchestrator Agent
- **Role**: Natural language understanding and task routing
- **Goal**: Understand user queries and coordinate appropriate responses
- **Tools**: WebSearchTool (for clarification)

### Database Layer

- **SQLite**: Local database for development
- **Repository Pattern**: Abstracted database operations
- **Pydantic Models**: Type-safe data validation

## API Endpoints

### Recipes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recipes` | List recipes with filters |
| GET | `/api/recipes/{id}` | Get recipe by ID |
| POST | `/api/recipes` | Create recipe |
| PUT | `/api/recipes/{id}` | Update recipe |
| DELETE | `/api/recipes/{id}` | Delete recipe |
| POST | `/api/recipes/discover` | Discover recipes via AI |

### Meal Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/meal-plans` | List meal plans |
| GET | `/api/meal-plans/{id}` | Get meal plan by ID |
| POST | `/api/meal-plans` | Create meal plan via AI |
| DELETE | `/api/meal-plans/{id}` | Delete meal plan |

### Grocery Lists
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/grocery-lists` | List grocery lists |
| GET | `/api/grocery-lists/{id}` | Get grocery list by ID |
| POST | `/api/grocery-lists` | Generate from meal plan |
| PUT | `/api/grocery-lists/{id}/items/{item_id}` | Update item |
| DELETE | `/api/grocery-lists/{id}` | Delete grocery list |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Chat with SSE streaming |
| POST | `/api/chat/sync` | Chat (non-streaming) |

## Data Models

### Recipe
```python
class Recipe:
    id: int
    name: str
    description: str
    ingredients: List[RecipeIngredient]
    instructions: List[str]
    prep_time: int  # minutes
    cook_time: int  # minutes
    servings: int
    difficulty: DifficultyLevel
    cuisine: CuisineType
    dietary_tags: List[DietaryTag]
    nutritional_info: NutritionalInfo
```

### MealPlan
```python
class MealPlan:
    id: int
    name: str
    start_date: date
    end_date: date
    meals: List[Meal]
    people_count: int
    dietary_restrictions: List[str]
```

### GroceryList
```python
class GroceryList:
    id: int
    meal_plan_id: int
    items: List[GroceryItem]
    estimated_cost: float
    completed: bool
```

## Development Workflow

### Running the Backend
```bash
cd backend
uv sync
uv run python run_api.py
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Running the Frontend
```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

### Running the CLI
```bash
cd backend
uv run python main.py chat
```

## Key Design Decisions

### Agent/API Separation
All LLM-dependent code is contained in `agents/` and `tasks/` directories, making future framework swaps easier. The service layer provides a clean interface between HTTP concerns and AI operations.

### Streaming Chat
The chat endpoint uses Server-Sent Events (SSE) for real-time token streaming, providing a better user experience with immediate feedback during AI processing.

### Minimal Agent Abstraction
CrewAI patterns are kept in dedicated modules without heavy abstraction layers. This maintains readability while keeping framework-specific code isolated.

## Future Enhancements

### Phase 2
- User authentication
- Advanced nutrition tracking
- Budget optimization
- Recipe image support

### Phase 3
- Voice interface
- Personalized AI learning
- Mobile app
- Social features (recipe sharing)
