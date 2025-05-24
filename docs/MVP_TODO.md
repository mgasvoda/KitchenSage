# KitchenCrew MVP Todo List

## Overview
This document outlines the tasks required to implement a Minimum Viable Product (MVP) for the KitchenCrew AI cooking assistant system.

## 🎯 MVP Goals
- [ ] Store and retrieve recipes from database
- [ ] Create basic meal plans 
- [ ] Generate grocery lists from meal plans
- [ ] Simple CLI interface for testing
- [ ] Basic recipe discovery (placeholder data)

---

## 🔥 Critical Priority (Must Complete First)

### 1. Fix Dependencies & Environment Setup
- [X] **Fix sqlite3 dependency** - Add back to requirements.txt (it's a built-in module but may need explicit handling)
- [ ] **Test installation process** - Verify all dependencies install correctly
- [X] **Create .env file** - Copy from env_example.txt and add placeholder API keys
- [X] **Test database initialization** - Run `python scripts/init_db.py` successfully

### 2. Implement Core Data Models ✅ COMPLETED
- [X] **Create `src/models/recipe.py`** - Recipe data model with Pydantic validation, enums, helper methods
- [X] **Create `src/models/ingredient.py`** - Ingredient models with categories, units, recipe ingredients
- [X] **Create `src/models/meal_plan.py`** - MealPlan and Meal models with date validation and utilities
- [X] **Create `src/models/grocery_list.py`** - GroceryList and GroceryItem models with shopping features
- [X] **Create `src/models/nutritional_info.py`** - Nutritional information model with macro calculations
- [X] **Create `src/models/__init__.py`** - Export all models and enums for easy importing

### 3. Implement Database Operations ✅ COMPLETED
- [X] **Create `src/database/connection.py`** - Database connection management with context managers, auto-commit/rollback
- [X] **Create `src/database/base_repository.py`** - Base repository class with common CRUD operations  
- [X] **Create `src/database/recipe_repository.py`** - Recipe CRUD operations with ingredient relationships
- [X] **Create `src/database/meal_plan_repository.py`** - Meal plan CRUD operations with meal relationships
- [X] **Create `src/database/grocery_repository.py`** - Grocery list CRUD operations with item management
- [X] **Create `src/database/__init__.py`** - Export database classes and connection utilities

### 4. Fix Tool Implementations
- [ ] **Update `DatabaseTool`** - Connect to actual database operations
- [ ] **Update `RecipeValidatorTool`** - Implement basic recipe validation
- [ ] **Update `RecipeSearchTool`** - Implement database search functionality
- [ ] **Update `MealPlanningTool`** - Basic meal plan creation logic
- [ ] **Update `ListOptimizationTool`** - Basic grocery list generation

---

## 🚀 High Priority (Core MVP Features)

### 5. Recipe Management System
- [ ] **Implement recipe storage** - Save recipes to database with validation
- [ ] **Implement recipe retrieval** - Get recipes by ID, filters, search terms
- [ ] **Add sample recipes** - Create 20-30 sample recipes for testing
- [ ] **Recipe validation logic** - Ensure required fields, validate data types
- [ ] **Ingredient normalization** - Standardize ingredient names and units

### 6. Meal Planning System
- [ ] **Basic meal plan creation** - Generate simple meal plans
- [ ] **Recipe selection logic** - Choose recipes based on criteria
- [ ] **Nutritional balance** - Basic calorie and macro tracking
- [ ] **Meal plan storage** - Save and retrieve meal plans from database
- [ ] **Date/calendar integration** - Assign recipes to specific days

### 7. Grocery List Generation
- [ ] **Extract ingredients from meal plans** - Parse all recipes in a meal plan
- [ ] **Consolidate ingredients** - Combine duplicate ingredients with quantities
- [ ] **Basic categorization** - Group items by store sections
- [ ] **Generate shopping list** - Create formatted grocery list output

### 8. CLI Interface for Testing
- [ ] **Create `src/cli.py`** - Command-line interface for MVP testing
- [ ] **Add recipe commands** - `add-recipe`, `list-recipes`, `search-recipes`
- [ ] **Add meal plan commands** - `create-meal-plan`, `show-meal-plan`
- [ ] **Add grocery commands** - `generate-grocery-list`, `show-grocery-list`
- [ ] **Update main.py** - Support CLI mode vs demo mode

---

## 🎨 Medium Priority (Polish & Enhancement)

### 9. Error Handling & Validation
- [ ] **Add input validation** - Validate all user inputs and API calls
- [ ] **Error handling in agents** - Graceful failure handling in CrewAI agents
- [ ] **Database error handling** - Handle connection issues, constraint violations
- [ ] **Logging improvements** - Add structured logging throughout application
- [ ] **User-friendly error messages** - Clear error messages for end users

### 10. Basic Testing
- [ ] **Create `tests/test_models.py`** - Test data models
- [ ] **Create `tests/test_database.py`** - Test database operations
- [ ] **Create `tests/test_tools.py`** - Test tool implementations
- [ ] **Create `tests/test_agents.py`** - Test agent interactions
- [ ] **Create `tests/test_cli.py`** - Test CLI functionality

### 11. Sample Data & Demo
- [ ] **Create sample recipe data** - JSON file with diverse recipes
- [ ] **Data import script** - Load sample recipes into database
- [ ] **Demo scenarios** - Pre-defined meal planning scenarios
- [ ] **Export functionality** - Export meal plans and grocery lists to JSON/CSV

---

## 🔮 Low Priority (Future Enhancements)

### 12. External Recipe Discovery
- [ ] **Mock API responses** - Simulate external recipe sources for testing
- [ ] **Recipe API integration** - Connect to Spoonacular or Edamam (optional)
- [ ] **Web scraping** - Basic recipe extraction from cooking websites
- [ ] **Content filtering** - Quality control for external recipes

### 13. Advanced Features
- [ ] **Nutritional analysis** - Detailed macro/micronutrient tracking
- [ ] **Dietary restriction handling** - Advanced filtering and substitutions
- [ ] **Budget optimization** - Cost-aware meal planning
- [ ] **Seasonal ingredients** - Ingredient availability and pricing
- [ ] **Recipe recommendations** - ML-based recipe suggestions

### 14. User Interface
- [ ] **Web interface** - Simple Flask/FastAPI web UI
- [ ] **Recipe cards** - Formatted recipe display
- [ ] **Meal plan calendar** - Visual meal planning interface
- [ ] **Grocery list checkboxes** - Interactive shopping list

---

## 📋 Implementation Order

### Phase 1: Foundation (Week 1)
1. Fix dependencies and environment
2. Implement data models
3. Set up database operations
4. Fix tool implementations

### Phase 2: Core Features (Week 2)
1. Recipe management system
2. Basic meal planning
3. Grocery list generation
4. CLI interface

### Phase 3: Testing & Polish (Week 3)
1. Error handling and validation
2. Basic testing
3. Sample data and demo scenarios
4. Documentation updates

### Phase 4: Enhancement (Optional)
1. External recipe discovery
2. Advanced features
3. User interface improvements

---

## 🧪 Testing Strategy

### Manual Testing Checklist
- [ ] **Add a recipe** - Manually add a recipe through CLI
- [ ] **Search recipes** - Find recipes by ingredient, cuisine, dietary restrictions
- [ ] **Create meal plan** - Generate a 7-day meal plan for 2 people
- [ ] **Generate grocery list** - Create shopping list from meal plan
- [ ] **Database persistence** - Verify data persists between application runs

### Automated Testing Goals
- [ ] **Unit tests** - 80%+ code coverage for core functions
- [ ] **Integration tests** - Test agent workflows end-to-end
- [ ] **Database tests** - Test all CRUD operations
- [ ] **CLI tests** - Test command-line interface functionality

---

## 🎯 MVP Success Criteria

The MVP will be considered complete when:

1. ✅ **Recipe Management**: Can add, search, and retrieve recipes from database
2. ✅ **Meal Planning**: Can create a basic 7-day meal plan with balanced nutrition
3. ✅ **Grocery Lists**: Can generate organized shopping lists from meal plans
4. ✅ **CLI Interface**: Simple command-line interface for all operations
5. ✅ **Data Persistence**: All data persists in SQLite database
6. ✅ **Demo Ready**: Can demonstrate complete workflow from recipe to grocery list
7. ✅ **Error Handling**: Graceful handling of common errors and edge cases
8. ✅ **Documentation**: Updated README with installation and usage instructions

---

## 📝 Notes

- **CrewAI Integration**: Focus on getting basic agent orchestration working before advanced features
- **Database First**: Implement solid database layer before complex AI features
- **Simple Before Smart**: Get basic functionality working before adding intelligence
- **Test Early**: Add testing as you implement each component
- **Documentation**: Update README.md and architecture docs as you implement features

---

## 🚨 Known Issues to Address

1. **SQLite3 Import**: May need to handle sqlite3 import differently
2. **Tool Integration**: CrewAI tools need proper integration with database operations  
3. **Agent Task Flow**: Ensure tasks properly pass data between agents
4. **Environment Variables**: Validate all required environment variables are loaded
5. **Import Paths**: Verify all relative imports work correctly

---

*Last Updated: Generated from project analysis*
*Priority: Focus on Critical and High Priority items for MVP* 