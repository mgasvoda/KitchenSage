# Importing Recipes from Paprika

Import recipes from Paprika app exports (`.paprikarecipes` files) into KitchenSage.

## Quick Start

```bash
cd backend

# Test import (recommended first step)
uv run python scripts/import_paprika.py ~/Downloads/Export*.paprikarecipes --dry-run

# Import recipes
uv run python scripts/import_paprika.py ~/Downloads/Export*.paprikarecipes

# Skip recipes with duplicate names
uv run python scripts/import_paprika.py ~/Downloads/Export*.paprikarecipes --skip-duplicates
```

## Export from Paprika

In Paprika app: **File → Export → All Recipes**

This creates a file like `Export 2025-06-14 17.21.08 All Recipes.paprikarecipes`

## What Gets Imported

### Recipe Data
- Name, description, notes, source
- Prep/cook times (auto-parsed from various formats like "1 hr 30 min", "45 minutes")
- Servings (defaults to 4 if not specified)
- Instructions (automatically split into steps)
- **Auto-detected**: difficulty level, cuisine type, dietary tags

### Ingredients
- Name, quantity, unit, notes
- **Auto-detected**: category (produce, meat, dairy, spices, etc.)
- Handles fractions (1/2, 1 1/2) and 30+ measurement units

### Smart Features
- Time parsing: If only total_time exists, splits into prep (30%) and cook (70%)
- Default times: 15min prep + 30min cook if none specified
- Field truncation: Long text automatically truncated to database limits
- List handling: Multi-ingredient lines (e.g., "cilantro, onions, cheese for topping") parsed intelligently

## Example Output

```
============================================================
Paprika Recipe Import
============================================================
File: Export 2025-06-14 17.21.08 All Recipes.paprikarecipes
Skip duplicates: False

Found 148 recipes to import

[1/148] Processing: Sunday Gravy Pizza Sauce.paprikarecipe
  ✓ Imported: "Sunday Gravy" Pizza Sauce (ID: 1)
[2/148] Processing: Antoni Falafel Salad.paprikarecipe
  ✓ Imported: Antoni Falafel Salad (ID: 2)
...

============================================================
Import Summary
============================================================
Total recipes: 148
Imported: 148
Skipped: 0
Failed: 0
```

## Troubleshooting

### Start Fresh
```bash
cd backend
rm kitchen_crew.db
uv run python scripts/init_db.py
uv run python scripts/import_paprika.py <file> --dry-run
```

### View Only Errors
```bash
uv run python scripts/import_paprika.py <file> 2>&1 | grep "❌"
```

### Common Issues

**File not found**: Use absolute paths or paths relative to `backend/` directory

**Import fails partway**: Script continues with other recipes. Check error summary at end.

**Duplicate recipes**: Use `--skip-duplicates` or delete from database first

**Wrong ingredient parsing**: Edit recipes after import via API or web interface

**Incorrect times**: Script estimates if not provided in Paprika. Edit after import if needed.

## Auto-Detection Keywords

### Dietary Tags
Detected from recipe name, description, notes, and categories:
- vegetarian, vegan
- gluten-free, dairy-free, nut-free, soy-free, egg-free
- low-carb, keto, paleo, whole30
- low-sodium, low-fat, high-protein

### Cuisines
Detected from recipe name and description:
- American, Italian, Mexican, Chinese, Japanese, Indian
- French, Thai, Greek, Mediterranean, Spanish, German
- Korean, Vietnamese, Middle Eastern, African

### Ingredient Categories
Auto-categorized by keywords in ingredient names:
- **Meat**: chicken, beef, pork, lamb, turkey, sausage, bacon
- **Seafood**: fish, salmon, tuna, shrimp, crab, lobster
- **Dairy**: milk, cheese, butter, cream, yogurt
- **Produce**: tomato, onion, garlic, lettuce, carrot, potato
- **Spices**: salt, pepper, paprika, cumin, oregano, basil
- **Grains**: rice, pasta, bread, flour, oat, quinoa
- **Legumes**: bean, lentil, chickpea, pea
- **Baking**: sugar, baking powder, baking soda, yeast, vanilla
- **Condiments**: oil, vinegar, sauce, mustard, ketchup

## After Import

1. **Start services**:
   ```bash
   ./start.sh
   ```

2. **View recipes**:
   - API docs: http://localhost:8000/docs
   - Frontend: http://localhost:5173

3. **Verify import**:
   ```bash
   cd backend
   uv run python -c "
   import sqlite3
   conn = sqlite3.connect('kitchen_crew.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM recipes')
   print(f'Total recipes: {cursor.fetchone()[0]}')
   cursor.execute('SELECT COUNT(*) FROM ingredients')
   print(f'Total ingredients: {cursor.fetchone()[0]}')
   "
   ```

## Reference

- Script: `backend/scripts/import_paprika.py`
- Database init: `backend/scripts/init_db.py`
- Models: `backend/src/models/recipe.py`, `backend/src/models/ingredient.py`
- Repository: `backend/src/database/recipe_repository.py`
