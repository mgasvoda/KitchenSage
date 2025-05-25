# KitchenCrew - AI-Powered Cooking Assistant

KitchenCrew is an AI agent system built with the CrewAI framework that helps you manage recipes, create meal plans, discover new dishes, and generate grocery lists through a natural language chat interface.

## Features

- **🤖 Natural Language Interface**: Chat with AI agents using everyday language
- **Recipe Management**: Store and organize recipes in a SQLite database
- **Meal Planning**: Create weekly meal plans based on preferences and dietary restrictions
- **Recipe Discovery**: Find new recipes from various sources
- **Grocery List Generation**: Automatically generate shopping lists from meal plans
- **Smart Recommendations**: AI-powered suggestions based on ingredients, cuisine preferences, and dietary needs

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- uv package manager (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd KitchenCrew
```

2. Create and activate virtual environment:
```powershell
# Using uv (recommended)
uv venv
.venv\Scripts\Activate.ps1

# Or using pip
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:
```powershell
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp env_example.txt .env
# Edit .env with your API keys
```

5. Initialize the database:
```bash
python scripts/init_db.py
```

## Usage

### 🗣️ Chat Interface (Recommended)

Start the interactive chat interface where you can talk to KitchenCrew AI agents using natural language:

```powershell
# Start interactive chat
uv run python main.py chat

# Or ask a single question
uv run python main.py ask "find quick italian recipes for dinner"
```

#### Example Conversations

**Finding Recipes:**
```
You: find quick mediterranean recipes
🤖: I understand you want to: find recipes with: cuisine=mediterranean, max_prep_time=30
[AI agents search and return Mediterranean recipes under 30 minutes]

You: show me vegetarian meals under 45 minutes
🤖: I understand you want to: find recipes with: dietary_restrictions=['vegetarian'], max_prep_time=45
[AI agents return vegetarian recipes]
```

**Meal Planning:**
```
You: create a meal plan for this week for 4 people
🤖: I understand you want to: create meal plan with: days=7, people=4
[AI agents create a 7-day meal plan for 4 people]

You: plan meals for 5 days with a $150 budget
🤖: I understand you want to: create meal plan with: days=5, budget=150.0
[AI agents create budget-conscious meal plan]
```

**Recipe Suggestions:**
```
You: what can I make with chicken and rice?
🤖: I understand you want to: get suggestions with: ingredients=['chicken', 'rice']
[AI agents suggest recipes using available ingredients]
```

#### Supported Natural Language Commands

| Intent | Example Commands |
|--------|------------------|
| **Find Recipes** | "find quick italian recipes", "search for vegetarian meals", "show me gluten-free dishes" |
| **Meal Planning** | "create a meal plan for this week", "plan meals for 4 people", "build a 5-day meal plan" |
| **Grocery Lists** | "generate a grocery list", "create a shopping list", "what do I need to buy?" |
| **Recipe Suggestions** | "what can I make with tomatoes?", "suggest recipes using chicken", "recipe ideas for dinner" |
| **Add Recipes** | "add my grandmother's recipe", "save this new recipe" |

#### Chat Commands

- `help` - Show detailed help and examples
- `history` - View conversation history
- `quit` or `exit` - Exit the chat

### 🐍 Python API

You can also use KitchenCrew programmatically:

```python
from src.crew import KitchenCrew

# Initialize the crew
crew = KitchenCrew()

# Find new recipes
recipes = crew.find_recipes(cuisine="italian", dietary_restrictions=["vegetarian"])

# Create a meal plan
meal_plan = crew.create_meal_plan(days=7, people=4)

# Generate grocery list
grocery_list = crew.generate_grocery_list(meal_plan_id=1)
```

## Project Structure

```
KitchenCrew/
├── src/
│   ├── agents/           # CrewAI agents
│   ├── tasks/            # Task definitions
│   ├── tools/            # Custom tools
│   ├── database/         # Database models and operations
│   ├── models/           # Data models
│   ├── utils/            # Utility functions
│   └── cli.py            # Natural language CLI interface
├── scripts/              # Setup and utility scripts
├── tests/                # Test files
├── data/                 # Sample data and exports
├── docs/                 # Documentation
└── main.py               # Main entry point
```

## CLI Architecture

The CLI uses a sophisticated natural language processing system:

1. **CommandParser**: Analyzes user input using regex patterns to identify intent and extract parameters
2. **KitchenCrewCLI**: Manages the chat interface and conversation flow
3. **CrewAI Integration**: Routes parsed commands to appropriate AI agents through the KitchenCrew orchestrator
4. **Rich Display**: Provides beautiful, formatted output with colors, panels, and tables

### Supported Parameters

The CLI automatically extracts these parameters from natural language:

- **Cuisine Types**: italian, mexican, chinese, indian, french, thai, japanese, mediterranean, etc.
- **Dietary Restrictions**: vegetarian, vegan, gluten-free, dairy-free, keto, paleo, low-carb, etc.
- **Time Constraints**: "under 30 minutes", "quick", "fast", "2 hours"
- **Serving Sizes**: "for 4 people", "2 servings", "family of 6"
- **Budget**: "$100", "$50 budget"
- **Ingredients**: "with chicken and rice", "using tomatoes"

## Development

### Adding New Command Patterns

To add support for new natural language commands, update the `CommandParser` class in `src/cli.py`:

```python
# Add new patterns to the patterns dictionary
self.patterns['new_command'] = [
    r'pattern1.*regex',
    r'pattern2.*regex'
]

# Add parameter extraction in _extract_parameters method
```

### Testing the CLI

```powershell
# Test help command
uv run python main.py --help

# Test single command
uv run python main.py ask "find italian recipes"

# Start interactive session
uv run python main.py chat
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License 