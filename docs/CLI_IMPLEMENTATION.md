# KitchenCrew CLI Implementation

## Overview

The KitchenCrew CLI provides a natural language chat interface that allows users to interact with AI agents using everyday language instead of complex command-line arguments. Users can issue commands like "find quick mediterranean recipes" or "build a meal plan for this week that incorporates my homemade pizza recipe" and the system will parse these commands and route them to the appropriate CrewAI agents.

## Architecture

### 1. CommandParser Class

The `CommandParser` class is responsible for interpreting natural language input and extracting structured parameters:

```python
class CommandParser:
    def __init__(self):
        # Command patterns for different agent capabilities
        self.patterns = {
            'find_recipes': [...],
            'create_meal_plan': [...],
            'generate_grocery_list': [...],
            'add_recipe': [...],
            'get_suggestions': [...]
        }
        
        # Parameter extraction patterns
        self.param_patterns = {
            'cuisine': r'(italian|mexican|chinese|...)',
            'dietary': r'(vegetarian|vegan|gluten.?free|...)',
            'time': r'(\d+)\s*(minutes?|mins?|hours?|hrs?)',
            # ... more patterns
        }
```

**Key Features:**
- Uses regex patterns to identify command intent
- Extracts parameters like cuisine, dietary restrictions, time constraints, etc.
- Handles natural language variations and synonyms
- Provides fallback to recipe search for ambiguous commands

### 2. KitchenCrewCLI Class

The main CLI interface that manages the chat session and coordinates with the CrewAI agents:

```python
class KitchenCrewCLI:
    def __init__(self):
        self.console = Console()  # Rich console for beautiful output
        self.parser = CommandParser()
        self.crew = KitchenCrew()  # CrewAI orchestrator
        self.conversation_history = []
```

**Key Features:**
- Interactive chat loop with rich formatting
- Command history tracking
- Error handling and user feedback
- Integration with CrewAI orchestrator
- Beautiful output formatting with panels, tables, and colors

### 3. Integration with CrewAI

The CLI routes parsed commands to the appropriate CrewAI agents through the `KitchenCrew` orchestrator:

```python
def _execute_command(self, command_type: str, parameters: Dict[str, Any]):
    if command_type == 'find_recipes':
        return self.crew.find_recipes(**parameters)
    elif command_type == 'create_meal_plan':
        return self.crew.create_meal_plan(**parameters)
    # ... more command routing
```

## Natural Language Processing

### Supported Command Types

1. **Recipe Finding (General)**
   - Patterns: "find recipes", "search for", "show me", "discover"
   - Parameters: cuisine, dietary restrictions, time constraints, ingredients
   - **Behavior**: Uses both Recipe Scout (online) and Recipe Manager (database) agents

2. **Searching Stored Recipes**
   - Patterns: "what recipes do I have", "show my recipes", "list my recipes", "browse my recipes"
   - Parameters: cuisine, dietary restrictions, time constraints, ingredients
   - **Behavior**: Only searches the local database using Recipe Manager agent

3. **Discovering New Recipes Online**
   - Patterns: "find new recipes", "discover new recipes online", "search online for recipes", "explore new recipes"
   - Parameters: cuisine, dietary restrictions, time constraints, ingredients
   - **Behavior**: Only searches external sources using Recipe Scout agent, optionally stores results

4. **Meal Planning**
   - Patterns: "create meal plan", "plan meals", "weekly plan"
   - Parameters: days, people, budget, dietary restrictions

5. **Grocery Lists**
   - Patterns: "grocery list", "shopping list", "what to buy"
   - Parameters: meal plan ID

6. **Recipe Suggestions**
   - Patterns: "what can I make", "suggest recipes", "recommendations"
   - Parameters: available ingredients

7. **Recipe Addition**
   - Patterns: "add recipe", "save recipe", "new recipe"
   - Parameters: recipe data

### Command Distinction Logic

The CLI uses **pattern matching order** to distinguish between different types of recipe searches:

1. **Most Specific First**: `search_stored_recipes` and `discover_new_recipes` patterns are checked first
2. **General Fallback**: `find_recipes` patterns are checked last as a fallback

**Examples of Command Routing:**

| User Input | Detected Command | Agent(s) Used | Behavior |
|------------|------------------|---------------|----------|
| "what recipes do I have?" | `search_stored_recipes` | Recipe Manager only | Searches local database |
| "find new italian recipes" | `discover_new_recipes` | Recipe Scout + Recipe Manager | Searches online, optionally stores |
| "find italian recipes" | `find_recipes` | Recipe Scout + Recipe Manager | Searches both online and database |
| "show my vegetarian recipes" | `search_stored_recipes` | Recipe Manager only | Searches local database |
| "discover recipes online" | `discover_new_recipes` | Recipe Scout + Recipe Manager | Searches online sources |

### Agent Orchestration

**For Stored Recipe Searches:**
```python
# Only uses Recipe Manager agent
search_crew = Crew(
    agents=[self.recipe_manager.agent],
    tasks=[self.recipe_tasks.search_stored_recipes_task(...)]
)
```

**For New Recipe Discovery:**
```python
# Uses Recipe Scout + Recipe Manager for validation/storage
discovery_crew = Crew(
    agents=[self.recipe_scout.agent, self.recipe_manager.agent],
    tasks=[
        self.discovery_tasks.search_recipes_task(...),
        self.recipe_tasks.validate_and_store_recipes_task()
    ]
)
```

**For General Recipe Finding:**
```python
# Uses both agents for comprehensive search
discovery_crew = Crew(
    agents=[self.recipe_scout.agent, self.recipe_manager.agent],
    tasks=[
        self.discovery_tasks.search_recipes_task(...),
        self.recipe_tasks.validate_and_store_recipes_task()
    ]
)
```

### Parameter Extraction

The system automatically extracts these parameters from natural language:

| Parameter Type | Examples | Regex Pattern |
|----------------|----------|---------------|
| **Cuisine** | "italian", "mexican", "mediterranean" | `(italian\|mexican\|chinese\|...)` |
| **Dietary** | "vegetarian", "gluten-free", "keto" | `(vegetarian\|vegan\|gluten.?free\|...)` |
| **Time** | "30 minutes", "2 hours", "quick" | `(\d+)\s*(minutes?\|hours?)` |
| **People** | "4 people", "family of 6" | `(\d+)\s*(people\|persons?\|servings?)` |
| **Budget** | "$150", "100 dollars" | `\$(\d+(?:\.\d{2})?)\|(\d+)\s*dollars?` |
| **Ingredients** | "with chicken and rice" | `(?:with\|using)\s+([^.!?]+?)` |

### Smart Defaults

- "quick" or "fast" → max_prep_time = 30 minutes
- "this week" → days = 7
- "month" → days = 30
- Ambiguous commands default to recipe search

## Usage Examples

### Starting the CLI

```powershell
# Interactive chat mode
uv run python main.py chat

# Single command mode
uv run python main.py ask "find vegetarian recipes under 30 minutes"
```

### Example Conversations

**Recipe Discovery:**
```
You: find quick italian recipes
🤖: I understand you want to: find recipes with: cuisine=italian, max_prep_time=30
[AI agents search and return results]
```

**Meal Planning:**
```
You: create a meal plan for this week for 4 people with a $200 budget
🤖: I understand you want to: create meal plan with: days=7, people=4, budget=200.0
[AI agents create meal plan]
```

**Ingredient-Based Suggestions:**
```
You: what can I make with chicken and rice?
🤖: I understand you want to: get suggestions with: ingredients=['chicken', 'rice']
[AI agents suggest recipes]
```

## File Structure

```
src/
├── cli.py                 # Main CLI implementation
├── crew.py               # CrewAI orchestrator
├── agents/               # AI agents
├── tasks/                # Task definitions
└── models/               # Data models

# Entry points
main.py                   # Main CLI entry point
demo_cli.py              # Demo without full CrewAI setup
test_cli.py              # Command parsing tests
```

## Key Dependencies

- **click**: Command-line interface framework
- **rich**: Beautiful terminal output with colors, panels, tables
- **crewai**: AI agent orchestration framework
- **pydantic**: Data validation and modeling
- **python-dotenv**: Environment variable management

## Testing

### Command Parsing Tests

```powershell
uv run python test_cli.py
```

Tests various natural language inputs to ensure correct parsing:
- "find quick italian recipes" → find_recipes + cuisine=italian + max_prep_time=30
- "create a meal plan for 4 people" → create_meal_plan + people=4 + days=7
- "what can I make with chicken and rice?" → get_suggestions + ingredients=['chicken', 'rice']

### Demo Mode

```powershell
uv run python demo_cli.py
```

Interactive demo that shows command parsing without requiring full CrewAI setup.

## Future Enhancements

### 1. Enhanced NLP
- Integration with spaCy or NLTK for better entity recognition
- Support for more complex queries with multiple constraints
- Context awareness across conversation turns

### 2. Voice Interface
- Speech-to-text integration
- Voice responses using text-to-speech

### 3. Multi-language Support
- Support for commands in multiple languages
- Localized cuisine and ingredient recognition

### 4. Learning Capabilities
- Learn from user corrections and preferences
- Adaptive parsing based on user patterns

### 5. Advanced Features
- Recipe image recognition and description
- Integration with smart kitchen devices
- Nutritional analysis and health recommendations

## Error Handling

The CLI includes comprehensive error handling:

1. **Parsing Errors**: Graceful fallback to recipe search
2. **Agent Errors**: User-friendly error messages
3. **Network Issues**: Retry logic and offline mode
4. **Invalid Input**: Helpful suggestions and examples

## Performance Considerations

- **Lazy Loading**: Agents are initialized only when needed
- **Caching**: Frequently used data is cached
- **Async Operations**: Long-running tasks use async patterns
- **Resource Management**: Proper cleanup of database connections

## Security

- **Input Validation**: All user input is validated and sanitized
- **API Key Management**: Secure handling of API keys
- **Database Security**: Parameterized queries to prevent injection
- **Rate Limiting**: Protection against API abuse

This CLI implementation provides a natural, intuitive way for users to interact with the powerful KitchenCrew AI agent system, making advanced cooking assistance accessible through simple conversation. 