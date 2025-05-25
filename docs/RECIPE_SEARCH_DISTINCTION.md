# Recipe Search Distinction in KitchenCrew CLI

## Problem Statement

The original CLI implementation didn't distinguish between:
1. **Searching stored recipes** in the local database
2. **Discovering new recipes** from external sources online

This led to ambiguity when users wanted to specifically search their existing collection vs. find new recipes.

## Solution Overview

The enhanced CLI now provides **three distinct recipe search modes**:

### 1. 🔍 General Recipe Search (`find_recipes`)
- **Triggers**: "find recipes", "search for recipes", "show me recipes"
- **Behavior**: Searches both local database AND external sources
- **Agents Used**: Recipe Scout + Recipe Manager
- **Use Case**: When user wants comprehensive results from all sources

### 2. 📚 Stored Recipe Search (`search_stored_recipes`)
- **Triggers**: "what recipes do I have?", "show my recipes", "list my recipes"
- **Behavior**: Only searches local database
- **Agents Used**: Recipe Manager only
- **Use Case**: When user wants to see what they already have saved

### 3. 🌐 New Recipe Discovery (`discover_new_recipes`)
- **Triggers**: "find new recipes", "discover recipes online", "explore new recipes"
- **Behavior**: Only searches external sources, optionally stores results
- **Agents Used**: Recipe Scout + Recipe Manager (for storage)
- **Use Case**: When user specifically wants fresh, new recipe ideas

## Implementation Details

### Pattern Matching Strategy

The CLI uses **ordered pattern matching** where more specific patterns are checked first:

```python
self.patterns = {
    # Most specific patterns first
    'search_stored_recipes': [
        r'what.*recipes?.*(?:do\s+i\s+have|available|stored|saved)',
        r'show.*my.*recipes?',
        r'list.*my.*recipes?',
        # ...
    ],
    'discover_new_recipes': [
        r'find.*new.*recipes?',
        r'discover.*recipes?.*online',
        r'search.*(?:online|web|internet).*recipes?',
        # ...
    ],
    # General fallback pattern last
    'find_recipes': [
        r'find.*recipes?',
        r'search.*recipes?',
        # ...
    ]
}
```

### Agent Orchestration

Each command type uses different agent combinations:

**Stored Recipe Search:**
```python
def search_stored_recipes(self, ...):
    search_crew = Crew(
        agents=[self.recipe_manager.agent],  # Database only
        tasks=[self.recipe_tasks.search_stored_recipes_task(...)]
    )
```

**New Recipe Discovery:**
```python
def discover_new_recipes(self, ...):
    discovery_crew = Crew(
        agents=[self.recipe_scout.agent, self.recipe_manager.agent],
        tasks=[
            self.discovery_tasks.search_recipes_task(...),      # Online search
            self.recipe_tasks.validate_and_store_recipes_task() # Optional storage
        ]
    )
```

## User Experience Examples

### Example 1: Checking Existing Recipes
```
User: "what italian recipes do I have available?"
🤖: I understand you want to: search stored recipes with: cuisine=italian
[Recipe Manager searches local database only]
Result: 📚 Your Stored Recipes
```

### Example 2: Finding New Recipe Ideas
```
User: "discover new vegetarian recipes online"
🤖: I understand you want to: discover new recipes with: dietary_restrictions=['vegetarian']
[Recipe Scout searches external sources]
Result: 🌐 New Recipes Discovered
```

### Example 3: General Recipe Search
```
User: "find quick dinner recipes"
🤖: I understand you want to: find recipes with: max_prep_time=30
[Both Recipe Scout and Recipe Manager work together]
Result: 🍽️ Recipe Results (from all sources)
```

## Benefits

### 1. **Clear User Intent**
- Users can explicitly specify whether they want stored or new recipes
- Reduces confusion about search scope

### 2. **Efficient Resource Usage**
- Stored recipe searches don't make unnecessary API calls
- New recipe discovery focuses on external sources

### 3. **Better User Experience**
- Appropriate visual indicators (📚 vs 🌐 vs 🍽️)
- Faster responses for database-only searches
- Clear expectations about what will be searched

### 4. **Flexible Workflow**
- Users can start with stored recipes, then discover new ones
- Option to save newly discovered recipes for future use

## Testing

The implementation includes comprehensive tests to verify correct command routing:

```bash
uv run python test_cli.py
```

Test cases verify:
- ✅ "what recipes do I have?" → `search_stored_recipes`
- ✅ "find new recipes online" → `discover_new_recipes`
- ✅ "show my italian recipes" → `search_stored_recipes`
- ✅ "discover new vegetarian recipes" → `discover_new_recipes`
- ✅ "find quick recipes" → `find_recipes` (general)

## Future Enhancements

### 1. **Hybrid Search**
- Smart combination of stored and new recipes
- "Show me my pasta recipes and find 3 new ones"

### 2. **Search Preferences**
- User settings for default search behavior
- "Always search stored recipes first"

### 3. **Context Awareness**
- Remember previous search context
- "Find more like the last recipe you showed me"

### 4. **Advanced Filtering**
- "Show me stored recipes I haven't made in 6 months"
- "Find new recipes similar to my favorites"

This implementation provides a solid foundation for intelligent recipe search that respects user intent and optimizes resource usage while maintaining the natural language interface that makes KitchenCrew so user-friendly. 