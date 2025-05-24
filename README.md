# KitchenCrew - AI-Powered Cooking Assistant

KitchenCrew is an AI agent system built with the CrewAI framework that helps you manage recipes, create meal plans, discover new dishes, and generate grocery lists.

## Features

- **Recipe Management**: Store and organize recipes in a SQLite database
- **Meal Planning**: Create weekly meal plans based on preferences and dietary restrictions
- **Recipe Discovery**: Find new recipes from various sources
- **Grocery List Generation**: Automatically generate shopping lists from meal plans
- **Smart Recommendations**: AI-powered suggestions based on ingredients, cuisine preferences, and dietary needs

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd KitchenCrew
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env_example.txt .env
# Edit .env with your API keys
```

4. Initialize the database:
```bash
python scripts/init_db.py
```

5. Run the application:
```bash
python main.py
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
│   └── utils/            # Utility functions
├── scripts/              # Setup and utility scripts
├── tests/                # Test files
├── data/                 # Sample data and exports
└── docs/                 # Documentation
```

## Usage

### Basic Commands

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License 