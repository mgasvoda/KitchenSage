# KitchenCrew Orchestrator Agent Design

## Overview

The KitchenCrew Orchestrator Agent replaces the previous rule-based command parsing system with an AI-powered natural language understanding approach. This design is more aligned with the AI-agent nature of the project and provides much more flexible and intelligent query processing.

## Architecture

### Previous Approach (Rule-Based)
```
User Input → Regex Patterns → Parameter Extraction → Direct Method Calls
```

**Limitations:**
- Rigid pattern matching
- Limited natural language understanding
- Difficult to extend with new patterns
- Poor handling of ambiguous queries
- No context awareness

### New Approach (AI-Orchestrated)
```
User Input → Orchestrator Agent → Intent Analysis → Agent Coordination → Response
```

**Benefits:**
- Natural language understanding
- Context-aware conversations
- Intelligent clarification requests
- Flexible intent recognition
- Easy to extend with new capabilities

## Components

### 1. OrchestratorAgent (`src/agents/orchestrator.py`)

**Role**: KitchenCrew Query Orchestrator  
**Goal**: Understand user cooking requests and coordinate appropriate AI agents  

**Capabilities:**
- Natural language understanding of cooking-related queries
- Intent extraction and parameter identification
- Context awareness from conversation history
- Intelligent clarification when information is missing
- Coordination with specialized agents

**Tools:**
- WebSearchTool (for clarifying cooking terms or ingredients)

### 2. OrchestratorTasks (`src/tasks/orchestrator_tasks.py`)

#### `parse_user_query_task`
Analyzes user input and extracts:
- Primary intent (recipe search, meal planning, etc.)
- Parameters (cuisine, dietary restrictions, ingredients, etc.)
- Confidence level
- Required agents
- Need for clarification

**Output Format:**
```json
{
    "intent": "find_recipes",
    "confidence": "high",
    "parameters": {
        "cuisine": "italian",
        "dietary_restrictions": ["vegetarian"],
        "max_prep_time": 30
    },
    "agents_needed": ["recipe_scout"],
    "clarification_needed": false,
    "clarifying_questions": [],
    "reasoning": "User wants quick Italian vegetarian recipes"
}
```

#### `route_to_agents_task`
Coordinates execution with appropriate agents based on parsed intent.

#### `clarify_user_intent_task`
Generates friendly clarification questions when user intent is unclear.

### 3. OrchestratedKitchenCrewCLI (`src/cli_orchestrated.py`)

**Main CLI Interface** that orchestrates the entire conversation flow:

1. **Query Processing**: Uses orchestrator agent to understand user input
2. **Context Management**: Maintains conversation history for better understanding
3. **Clarification Handling**: Asks intelligent follow-up questions
4. **Agent Coordination**: Routes to appropriate KitchenCrew methods
5. **Response Display**: Presents results in user-friendly format

## Workflow

### 1. User Input Processing
```python
def _process_with_orchestrator(self, user_input: str):
    # Get conversation context
    context = self._get_conversation_context()
    
    # Parse query with orchestrator
    parsed_result = self._parse_user_query(user_input, context)
    
    # Handle clarification if needed
    if self._needs_clarification(parsed_result):
        self._handle_clarification(user_input, parsed_result)
        return
    
    # Execute with appropriate agents
    result = self._execute_parsed_request(parsed_result)
    
    # Display result
    self._display_result(result)
```

### 2. Intent Recognition
The orchestrator recognizes these primary intents:
- `find_recipes` - General recipe search
- `search_stored_recipes` - Search user's saved recipes
- `discover_new_recipes` - Find new recipes online
- `create_meal_plan` - Meal planning
- `generate_grocery_list` - Shopping list creation
- `add_recipe` - Recipe management
- `get_suggestions` - Recipe suggestions based on ingredients

### 3. Parameter Extraction
Automatically extracts cooking-related parameters:
- **Cuisine types**: italian, mexican, chinese, etc.
- **Dietary restrictions**: vegetarian, vegan, gluten-free, etc.
- **Time constraints**: quick, under 30 minutes, etc.
- **Serving information**: number of people, servings
- **Ingredients**: available ingredients to use
- **Budget constraints**: meal plan budgets
- **Meal types**: breakfast, lunch, dinner, snack

### 4. Context Awareness
The orchestrator maintains conversation context by:
- Tracking recent interactions
- Understanding follow-up questions
- Maintaining user preferences across the session
- Providing relevant clarifications

## Example Interactions

### Simple Recipe Search
```
User: "I want something quick with chicken"
Orchestrator: Extracts intent=find_recipes, ingredients=[chicken], max_prep_time=30
Result: Quick chicken recipes
```

### Ambiguous Query Requiring Clarification
```
User: "Plan my meals"
Orchestrator: Recognizes need for clarification
Response: "I'd be happy to help plan your meals! To create the best plan for you:
- How many days would you like me to plan for?
- How many people will be eating?
- Do you have any dietary restrictions or preferences?
- What's your approximate budget?"
```

### Context-Aware Follow-up
```
User: "Find Italian recipes"
Assistant: [Shows Italian recipes]
User: "Make them vegetarian"
Orchestrator: Uses context to understand this refers to Italian vegetarian recipes
```

## Benefits of the New Approach

### 1. Natural Language Understanding
- Users can speak naturally instead of learning command syntax
- Handles variations in phrasing and terminology
- Understands cooking context and terminology

### 2. Intelligent Clarification
- Asks relevant questions when information is missing
- Provides examples and options to help users
- Explains why information is needed

### 3. Context Awareness
- Remembers conversation history
- Understands follow-up questions and references
- Maintains user preferences during the session

### 4. Extensibility
- Easy to add new intents and capabilities
- No need to write complex regex patterns
- AI naturally handles new variations

### 5. Error Handling
- Graceful fallbacks when parsing fails
- Intelligent error messages
- Robust handling of edge cases

## Usage

### Starting the Orchestrated CLI
```bash
# Use the new orchestrated CLI (now default)
uv run python main.py chat

# Or directly
uv run python -m src.cli_orchestrated chat
```

### Testing the Orchestrator
```bash
# Run the test script
python test_orchestrator.py
```

## Migration from Rule-Based CLI

The original rule-based CLI (`src/cli.py`) is preserved for reference and comparison. The new orchestrated CLI (`src/cli_orchestrated.py`) is now the default interface.

### Key Differences:
- **Input Processing**: AI understanding vs regex patterns
- **Parameter Extraction**: Natural language analysis vs pattern matching
- **Extensibility**: Add new capabilities vs add new regex patterns
- **User Experience**: Conversational vs command-based

## Future Enhancements

1. **Learning from User Interactions**: Train the orchestrator on successful interactions
2. **Personalization**: Remember user preferences across sessions
3. **Multi-turn Conversations**: Handle complex multi-step cooking workflows
4. **Voice Integration**: Add speech-to-text for voice commands
5. **Recipe Recommendations**: Proactive suggestions based on user history 