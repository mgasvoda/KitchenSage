# KitchenCrew Agent-Tool Alignment

## Overview

This document outlines the alignment between KitchenCrew agents and their associated tools, ensuring each agent has access to the appropriate tools for their specialized functions.

## Agent-Tool Mapping

### 1. RecipeManagerAgent
**Role**: Recipe Database Manager  
**Goal**: Efficiently store, retrieve, and organize recipe data in the database

**Tools Available**:
- **DatabaseTool**: Core CRUD operations for all database entities
- **RecipeValidatorTool**: Validates recipe data for completeness and business rules
- **RecipeSearchTool**: Advanced search functionality with filtering and scoring

**Use Cases**:
- Store new recipes in database
- Validate recipe data before storage
- Search for recipes by various criteria
- Update and manage existing recipes

### 2. MealPlannerAgent
**Role**: Certified Nutritionist and Meal Planning Expert  
**Goal**: Create optimal meal plans based on nutritional needs, preferences, and constraints

**Tools Available**:
- **MealPlanningTool**: Creates optimized meal plans with recipe selection
- **NutritionAnalysisTool**: Analyzes nutritional content and provides recommendations
- **CalendarTool**: Schedules meals and manages meal plan calendars
- **RecipeSearchTool**: Finds suitable recipes for meal plan requirements

**Use Cases**:
- Create balanced meal plans for specific time periods
- Analyze nutritional content of meal plans
- Schedule meals on calendar with optimization
- Find recipes that match dietary requirements

### 3. GroceryListAgent
**Role**: Supply Chain Specialist and Shopping Optimization Expert  
**Goal**: Generate efficient and cost-optimized grocery lists from meal plans

**Tools Available**:
- **InventoryTool**: Manages pantry inventory to reduce unnecessary purchases
- **PriceComparisonTool**: Compares prices across stores for cost optimization
- **ListOptimizationTool**: Generates and optimizes grocery lists with shopping routes
- **DatabaseTool**: Accesses meal plan and recipe data for ingredient extraction

**Use Cases**:
- Extract ingredients from meal plans
- Generate optimized grocery lists
- Compare prices across stores
- Organize shopping lists by store sections

### 4. RecipeScoutAgent
**Role**: Culinary Researcher and Recipe Discovery Specialist  
**Goal**: Find and retrieve relevant recipes from various external sources

**Tools Available**:
- **WebScrapingTool**: Scrapes recipes from cooking websites
- **RecipeAPITool**: Accesses external recipe APIs (Spoonacular, Edamam, etc.)
- **ContentFilterTool**: Filters and validates external recipe content
- **DatabaseTool**: Stores discovered recipes in the database
- **RecipeValidatorTool**: Validates external recipes before storage

**Use Cases**:
- Discover new recipes from external sources
- Filter and validate external recipe content
- Store validated external recipes in database
- Find trending and seasonal recipes

## Tool Dependencies and Cross-Agent Collaboration

### Shared Tools
Several tools are shared across agents to enable collaboration:

- **DatabaseTool**: Used by RecipeManagerAgent, GroceryListAgent, and RecipeScoutAgent
- **RecipeValidatorTool**: Used by RecipeManagerAgent and RecipeScoutAgent
- **RecipeSearchTool**: Used by RecipeManagerAgent and MealPlannerAgent

### Workflow Integration
The agents are designed to work together in typical workflows:

1. **Recipe Discovery → Storage → Meal Planning → Grocery Shopping**:
   - RecipeScoutAgent discovers and validates external recipes
   - RecipeManagerAgent stores and organizes recipes
   - MealPlannerAgent creates meal plans using stored recipes
   - GroceryListAgent generates shopping lists from meal plans

2. **Recipe Management → Meal Planning**:
   - RecipeManagerAgent manages recipe database
   - MealPlannerAgent searches for suitable recipes for meal plans

3. **Meal Planning → Grocery List Generation**:
   - MealPlannerAgent creates meal plans
   - GroceryListAgent extracts ingredients and optimizes shopping

## Tool Implementation Status

All tools are fully implemented with the following capabilities:

### Database Tools ✅
- **DatabaseTool**: Complete CRUD operations with repository pattern
- **RecipeValidatorTool**: Business rule validation and data quality checks
- **RecipeSearchTool**: Advanced search with filtering and relevance scoring

### Meal Planning Tools ✅
- **MealPlanningTool**: Comprehensive meal plan creation with optimization
- **NutritionAnalysisTool**: Detailed nutritional analysis and recommendations
- **CalendarTool**: Meal scheduling with multiple calendar views

### Grocery Tools ✅
- **InventoryTool**: Mock inventory management with CRUD operations
- **PriceComparisonTool**: Multi-store price comparison with savings analysis
- **ListOptimizationTool**: Advanced grocery list optimization with routing

### Web Tools ✅
- **WebScrapingTool**: Placeholder implementation for website scraping
- **RecipeAPITool**: Mock API integration framework
- **ContentFilterTool**: Basic content validation and filtering

## Integration Testing

All agents have been tested for:
- ✅ Successful instantiation with their assigned tools
- ✅ Correct tool import paths and dependencies
- ✅ Tool compatibility and expected functionality
- ✅ Agent collection functions for orchestration

## Usage Examples

### Instantiating Individual Agents
```python
from src.agents import RecipeManagerAgent, MealPlannerAgent

# Create individual agents
recipe_manager = RecipeManagerAgent()
meal_planner = MealPlannerAgent()
```

### Using Agent Collection Functions
```python
from src.agents import get_all_agents, get_core_agents

# Get all agents for complete workflows
all_agents = get_all_agents()

# Get core agents for basic functionality
core_agents = get_core_agents()
```

### Accessing Agent Tools
```python
recipe_manager = RecipeManagerAgent()
available_tools = recipe_manager.tools
tool_names = [tool.name for tool in available_tools]
```

## Future Enhancements

### Planned Tool Additions
- **SeasonalIngredientTool**: Track seasonal ingredient availability
- **BudgetOptimizationTool**: Advanced budget-aware meal planning
- **SubstitutionTool**: Intelligent ingredient substitution recommendations

### Agent Enhancements
- **Enhanced Recipe Discovery**: More sophisticated external source integration
- **Advanced Nutrition Tracking**: Micronutrient analysis and dietary goal tracking
- **Smart Shopping**: Integration with store loyalty programs and real-time pricing

## Configuration

### Environment Requirements
- OpenAI API key for full AI functionality (optional - basic functionality available without)
- Database connection for persistent storage
- Python dependencies: crewai, pydantic, langchain-openai

### Agent Initialization
All agents check for OpenAI API availability and gracefully degrade to basic functionality if not available, ensuring the system works even without AI capabilities.

---

*Last Updated: Agent-tool integration completed and tested*
*Status: ✅ All agents properly aligned with their tools* 