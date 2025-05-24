"""
Grocery tools for shopping list generation and optimization.
"""

from crewai.tools import BaseTool
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

from src.database import RecipeRepository, MealPlanRepository, GroceryRepository
from src.models import (
    GroceryList, GroceryListCreate, GroceryItem, GroceryItemCreate,
    IngredientCategory, MeasurementUnit
)

logger = logging.getLogger(__name__)


class InventoryTool(BaseTool):
    """Tool for managing pantry inventory and ingredient tracking."""
    
    name: str = "Inventory Tool"
    description: str = "Manages pantry inventory and tracks available ingredients to optimize grocery lists."
    
    def _run(self, operation: str, ingredient: Optional[str] = None, 
             quantity: Optional[float] = None) -> Dict[str, Any]:
        """
        Manage inventory operations.
        
        Args:
            operation: Type of operation (check, add, remove, list)
            ingredient: Ingredient name for specific operations
            quantity: Quantity for add/remove operations
            
        Returns:
            Inventory operation result
        """
        # Placeholder implementation - this would integrate with a real inventory system
        # For MVP, we'll simulate basic inventory operations
        
        mock_inventory = {
            "salt": 1000,  # grams
            "black pepper": 50,  # grams
            "olive oil": 500,  # ml
            "garlic": 5,  # cloves
            "onion": 3,  # pieces
        }
        
        try:
            if operation == "check":
                if ingredient:
                    available_qty = mock_inventory.get(ingredient.lower(), 0)
                    return {
                        "status": "success",
                        "operation": "check",
                        "ingredient": ingredient,
                        "available_quantity": available_qty,
                        "in_stock": available_qty > 0,
                        "message": f"Checked inventory for {ingredient}"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Ingredient name required for check operation"
                    }
            
            elif operation == "list":
                return {
                    "status": "success",
                    "operation": "list",
                    "current_inventory": mock_inventory,
                    "total_items": len(mock_inventory),
                    "message": "Retrieved complete inventory"
                }
            
            elif operation in ["add", "remove"]:
                if not ingredient or quantity is None:
                    return {
                        "status": "error",
                        "message": f"{operation.capitalize()} operation requires ingredient and quantity"
                    }
                
                current_qty = mock_inventory.get(ingredient.lower(), 0)
                if operation == "add":
                    new_qty = current_qty + quantity
                else:  # remove
                    new_qty = max(0, current_qty - quantity)
                
                mock_inventory[ingredient.lower()] = new_qty
                
                return {
                    "status": "success",
                    "operation": operation,
                    "ingredient": ingredient,
                    "previous_quantity": current_qty,
                    "new_quantity": new_qty,
                    "message": f"{operation.capitalize()}ed {quantity} of {ingredient}"
                }
            
            else:
                return {
                    "status": "error",
                    "message": f"Unknown operation: {operation}. Valid operations: check, add, remove, list"
                }
                
        except Exception as e:
            logger.error(f"Inventory operation failed: {e}")
            return {
                "status": "error",
                "message": f"Inventory operation failed: {str(e)}"
            }


class PriceComparisonTool(BaseTool):
    """Tool for comparing grocery prices across different stores."""
    
    name: str = "Price Comparison Tool"
    description: str = "Compares prices of grocery items across different stores to find the best deals."
    
    def _run(self, ingredients: List[str], stores: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare prices across stores.
        
        Args:
            ingredients: List of ingredients to price check
            stores: Optional list of specific stores to check
            
        Returns:
            Price comparison results
        """
        # Mock price data - in a real implementation, this would query price APIs or databases
        mock_stores = stores or ["grocery_mart", "fresh_foods", "budget_market", "organic_plus"]
        
        # Mock price database (price per unit)
        mock_prices = {
            "chicken breast": {"grocery_mart": 8.99, "fresh_foods": 9.49, "budget_market": 7.99, "organic_plus": 12.99},
            "ground beef": {"grocery_mart": 6.99, "fresh_foods": 7.49, "budget_market": 5.99, "organic_plus": 9.99},
            "salmon": {"grocery_mart": 14.99, "fresh_foods": 16.99, "budget_market": 13.99, "organic_plus": 18.99},
            "rice": {"grocery_mart": 2.99, "fresh_foods": 3.49, "budget_market": 2.49, "organic_plus": 4.99},
            "pasta": {"grocery_mart": 1.99, "fresh_foods": 2.29, "budget_market": 1.79, "organic_plus": 3.49},
            "tomatoes": {"grocery_mart": 3.99, "fresh_foods": 4.49, "budget_market": 3.49, "organic_plus": 5.99},
            "onions": {"grocery_mart": 2.49, "fresh_foods": 2.79, "budget_market": 1.99, "organic_plus": 3.49},
            "bread": {"grocery_mart": 2.99, "fresh_foods": 3.49, "budget_market": 2.49, "organic_plus": 4.99},
            "milk": {"grocery_mart": 3.49, "fresh_foods": 3.79, "budget_market": 2.99, "organic_plus": 5.49},
            "eggs": {"grocery_mart": 3.99, "fresh_foods": 4.29, "budget_market": 3.49, "organic_plus": 6.99},
        }
        
        try:
            price_comparison = {}
            total_savings = 0
            best_overall_store = defaultdict(int)
            
            for ingredient in ingredients:
                ingredient_lower = ingredient.lower()
                ingredient_prices = {}
                
                # Get prices for this ingredient across stores
                if ingredient_lower in mock_prices:
                    store_prices = mock_prices[ingredient_lower]
                    
                    for store in mock_stores:
                        if store in store_prices:
                            ingredient_prices[store] = store_prices[store]
                    
                    if ingredient_prices:
                        # Find best price and store
                        best_price = min(ingredient_prices.values())
                        best_store = min(ingredient_prices.items(), key=lambda x: x[1])[0]
                        worst_price = max(ingredient_prices.values())
                        
                        savings = worst_price - best_price
                        total_savings += savings
                        best_overall_store[best_store] += 1
                        
                        price_comparison[ingredient] = {
                            "prices": ingredient_prices,
                            "best_price": best_price,
                            "best_store": best_store,
                            "worst_price": worst_price,
                            "potential_savings": round(savings, 2),
                            "price_range": f"${best_price:.2f} - ${worst_price:.2f}"
                        }
                    else:
                        price_comparison[ingredient] = {
                            "prices": {},
                            "message": f"No price data available for {ingredient} in selected stores"
                        }
                else:
                    # Generate mock prices for unknown ingredients
                    base_price = 3.99  # Default base price
                    ingredient_prices = {}
                    
                    for store in mock_stores:
                        # Add some variation to mock prices
                        variation = 0.1 + (hash(store + ingredient) % 100) / 100  # 0.1 to 1.1
                        store_price = base_price * variation
                        ingredient_prices[store] = round(store_price, 2)
                    
                    best_price = min(ingredient_prices.values())
                    best_store = min(ingredient_prices.items(), key=lambda x: x[1])[0]
                    worst_price = max(ingredient_prices.values())
                    savings = worst_price - best_price
                    total_savings += savings
                    best_overall_store[best_store] += 1
                    
                    price_comparison[ingredient] = {
                        "prices": ingredient_prices,
                        "best_price": best_price,
                        "best_store": best_store,
                        "worst_price": worst_price,
                        "potential_savings": round(savings, 2),
                        "price_range": f"${best_price:.2f} - ${worst_price:.2f}",
                        "note": "Estimated prices - actual prices may vary"
                    }
            
            # Determine best overall store
            recommended_store = max(best_overall_store.items(), key=lambda x: x[1])[0] if best_overall_store else mock_stores[0]
            
            return {
                "status": "success",
                "price_comparison": price_comparison,
                "total_potential_savings": round(total_savings, 2),
                "recommended_store": recommended_store,
                "stores_checked": mock_stores,
                "best_deals_by_store": dict(best_overall_store),
                "message": f"Price comparison completed for {len(ingredients)} ingredients across {len(mock_stores)} stores"
            }
            
        except Exception as e:
            logger.error(f"Price comparison failed: {e}")
            return {
                "status": "error",
                "message": f"Price comparison failed: {str(e)}"
            }


class ListOptimizationTool(BaseTool):
    """Tool for optimizing grocery lists for efficient shopping."""
    
    name: str = "List Optimization Tool"
    description: str = "Optimizes grocery lists by grouping items, suggesting routes, and identifying bulk purchase opportunities."
    
    def _get_repositories(self):
        """Get repository instances (lazy initialization)."""
        if not hasattr(self, '_repos'):
            self._repos = {
                'meal_plans': MealPlanRepository(),
                'recipes': RecipeRepository(),
                'grocery_lists': GroceryRepository()
            }
        return self._repos
    
    def _run(self, meal_plan_id: Optional[int] = None, 
             grocery_list: Optional[List[Dict[str, Any]]] = None,
             preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate and optimize grocery list from meal plan or existing list.
        
        Args:
            meal_plan_id: ID of meal plan to generate grocery list from
            grocery_list: Existing grocery list to optimize (alternative to meal_plan_id)
            preferences: Shopping preferences (budget, stores, dietary restrictions, etc.)
            
        Returns:
            Optimized grocery list with shopping strategy
        """
        try:
            preferences = preferences or {}
            
            # Get ingredients list
            if meal_plan_id:
                ingredients_list = self._extract_ingredients_from_meal_plan(meal_plan_id)
            elif grocery_list:
                ingredients_list = self._parse_grocery_list(grocery_list)
            else:
                return {
                    "status": "error",
                    "message": "Either meal_plan_id or grocery_list must be provided"
                }
            
            if not ingredients_list:
                return {
                    "status": "error",
                    "message": "No ingredients found to create grocery list"
                }
            
            # Consolidate duplicate ingredients
            consolidated_ingredients = self._consolidate_ingredients(ingredients_list)
            
            # Apply inventory reduction if available
            if preferences.get('check_inventory', False):
                consolidated_ingredients = self._reduce_by_inventory(consolidated_ingredients)
            
            # Categorize and organize items
            organized_list = self._organize_by_category(consolidated_ingredients)
            
            # Generate shopping route
            shopping_route = self._generate_shopping_route(organized_list)
            
            # Identify bulk opportunities
            bulk_opportunities = self._identify_bulk_opportunities(consolidated_ingredients)
            
            # Calculate estimates
            cost_estimate = self._estimate_total_cost(consolidated_ingredients, preferences)
            time_estimate = self._estimate_shopping_time(consolidated_ingredients, preferences)
            
            # Create grocery list in database if meal_plan_id provided
            grocery_list_id = None
            if meal_plan_id:
                grocery_list_data = {
                    'meal_plan_id': meal_plan_id,
                    'estimated_cost': cost_estimate,
                    'items': [
                        {
                            'name': item['name'],
                            'quantity': item['quantity'],
                            'unit': item['unit'],
                            'category': item['category'],
                            'estimated_price': item.get('estimated_price', 0),
                            'notes': item.get('notes', '')
                        }
                        for item in consolidated_ingredients
                    ]
                }
                grocery_list_id = self._get_repositories()['grocery_lists'].create(grocery_list_data)
            
            return {
                "status": "success",
                "grocery_list_id": grocery_list_id,
                "optimized_list": organized_list,
                "consolidated_ingredients": consolidated_ingredients,
                "shopping_route": shopping_route,
                "bulk_opportunities": bulk_opportunities,
                "estimated_total_cost": cost_estimate,
                "estimated_shopping_time": time_estimate,
                "optimization_summary": {
                    "total_items": len(consolidated_ingredients),
                    "categories": len(organized_list),
                    "bulk_items": len(bulk_opportunities),
                    "estimated_savings": sum(item.get('bulk_savings', 0) for item in bulk_opportunities)
                },
                "shopping_tips": self._generate_shopping_tips(organized_list, preferences),
                "message": f"Grocery list optimized with {len(consolidated_ingredients)} items across {len(organized_list)} categories"
            }
            
        except Exception as e:
            logger.error(f"Grocery list optimization failed: {e}")
            return {
                "status": "error",
                "message": f"Grocery list optimization failed: {str(e)}"
            }
    
    def _extract_ingredients_from_meal_plan(self, meal_plan_id: int) -> List[Dict[str, Any]]:
        """Extract all ingredients from meals in a meal plan."""
        try:
            meal_plan = self._get_repositories()['meal_plans'].get_by_id(meal_plan_id)
            if not meal_plan:
                raise ValueError(f"Meal plan {meal_plan_id} not found")
            
            all_ingredients = []
            meals = meal_plan.get('meals', [])
            
            for meal in meals:
                recipe_id = meal.get('recipe_id')
                if recipe_id:
                    recipe = self._get_repositories()['recipes'].get_by_id(recipe_id)
                    if recipe and recipe.get('ingredients'):
                        servings_multiplier = meal.get('servings', 1) / recipe.get('servings', 1)
                        
                        for ingredient in recipe['ingredients']:
                            all_ingredients.append({
                                'name': ingredient.get('name'),
                                'quantity': ingredient.get('quantity', 0) * servings_multiplier,
                                'unit': ingredient.get('unit'),
                                'category': ingredient.get('category', 'other'),
                                'recipe_name': recipe.get('name'),
                                'meal_type': meal.get('meal_type'),
                                'meal_date': meal.get('date')
                            })
            
            return all_ingredients
            
        except Exception as e:
            logger.error(f"Failed to extract ingredients from meal plan {meal_plan_id}: {e}")
            return []
    
    def _parse_grocery_list(self, grocery_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse and standardize grocery list format."""
        standardized_list = []
        
        for item in grocery_list:
            standardized_item = {
                'name': item.get('name', '').strip(),
                'quantity': float(item.get('quantity', 1)),
                'unit': item.get('unit', 'piece').strip(),
                'category': item.get('category', 'other').strip(),
                'notes': item.get('notes', '').strip()
            }
            
            if standardized_item['name']:
                standardized_list.append(standardized_item)
        
        return standardized_list
    
    def _consolidate_ingredients(self, ingredients_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate duplicate ingredients with quantity conversion."""
        consolidated = {}
        
        for ingredient in ingredients_list:
            name = ingredient['name'].lower().strip()
            unit = ingredient.get('unit', 'piece').lower().strip()
            category = ingredient.get('category', 'other')
            
            # Create a key for grouping similar ingredients
            key = f"{name}_{unit}"
            
            if key not in consolidated:
                consolidated[key] = {
                    'name': ingredient['name'],
                    'quantity': 0,
                    'unit': unit,
                    'category': category,
                    'sources': [],
                    'notes': []
                }
            
            # Add quantity (handle unit conversion if needed)
            quantity_to_add = self._convert_quantity(
                ingredient.get('quantity', 0), 
                ingredient.get('unit', 'piece'), 
                unit
            )
            
            consolidated[key]['quantity'] += quantity_to_add
            
            # Track sources for transparency
            source_info = []
            if ingredient.get('recipe_name'):
                source_info.append(f"Recipe: {ingredient['recipe_name']}")
            if ingredient.get('meal_type'):
                source_info.append(f"Meal: {ingredient['meal_type']}")
            if ingredient.get('meal_date'):
                source_info.append(f"Date: {ingredient['meal_date']}")
            
            if source_info:
                consolidated[key]['sources'].append(" | ".join(source_info))
            
            # Collect notes
            if ingredient.get('notes'):
                consolidated[key]['notes'].append(ingredient['notes'])
        
        # Convert back to list and clean up
        result = []
        for item in consolidated.values():
            item['quantity'] = round(item['quantity'], 2)
            item['sources'] = list(set(item['sources']))  # Remove duplicates
            item['notes'] = list(set(item['notes']))  # Remove duplicates
            
            # Estimate price
            item['estimated_price'] = self._estimate_item_price(item['name'], item['quantity'], item['unit'])
            
            result.append(item)
        
        # Sort by category and name
        return sorted(result, key=lambda x: (x['category'], x['name']))
    
    def _convert_quantity(self, quantity: float, from_unit: str, to_unit: str) -> float:
        """Convert quantity between units where possible."""
        if from_unit.lower() == to_unit.lower():
            return quantity
        
        # Basic unit conversions (expand as needed)
        conversions = {
            ('gram', 'kg'): 0.001,
            ('kg', 'gram'): 1000,
            ('ml', 'liter'): 0.001,
            ('liter', 'ml'): 1000,
            ('tsp', 'tbsp'): 0.333,
            ('tbsp', 'tsp'): 3,
            ('cup', 'ml'): 240,
            ('ml', 'cup'): 1/240,
        }
        
        conversion_key = (from_unit.lower(), to_unit.lower())
        if conversion_key in conversions:
            return quantity * conversions[conversion_key]
        
        # If no conversion available, return original quantity
        return quantity
    
    def _reduce_by_inventory(self, ingredients_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Reduce ingredient quantities based on available inventory."""
        # This would integrate with the InventoryTool in a real implementation
        # For now, simulate some basic inventory reductions
        
        common_pantry_items = {
            'salt': 1000,  # grams
            'pepper': 50,
            'olive oil': 500,  # ml
            'garlic': 5,  # cloves
            'onion': 3,  # pieces
        }
        
        reduced_list = []
        for item in ingredients_list:
            name_lower = item['name'].lower()
            if name_lower in common_pantry_items:
                available_qty = common_pantry_items[name_lower]
                needed_qty = item['quantity']
                
                if available_qty >= needed_qty:
                    # Skip this item - we have enough in inventory
                    item['quantity'] = 0
                    item['notes'].append(f"Available in inventory ({available_qty} {item['unit']})")
                else:
                    # Reduce quantity needed
                    item['quantity'] = needed_qty - available_qty
                    item['notes'].append(f"Reduced by inventory ({available_qty} {item['unit']} available)")
            
            if item['quantity'] > 0:
                reduced_list.append(item)
        
        return reduced_list
    
    def _organize_by_category(self, ingredients_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize ingredients by store category/section."""
        
        # Map ingredient categories to store sections
        category_mapping = {
            'protein': 'Meat & Seafood',
            'dairy': 'Dairy & Eggs',
            'vegetable': 'Produce',
            'fruit': 'Produce',
            'grain': 'Pantry & Dry Goods',
            'spice': 'Pantry & Dry Goods',
            'condiment': 'Pantry & Dry Goods',
            'herb': 'Produce',
            'frozen': 'Frozen Foods',
            'beverage': 'Beverages',
            'other': 'Miscellaneous'
        }
        
        organized = defaultdict(list)
        
        for item in ingredients_list:
            category = item.get('category', 'other').lower()
            store_section = category_mapping.get(category, 'Miscellaneous')
            organized[store_section].append(item)
        
        # Sort items within each category
        for section in organized:
            organized[section].sort(key=lambda x: x['name'])
        
        return dict(organized)
    
    def _generate_shopping_route(self, organized_list: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate efficient shopping route through store sections."""
        
        # Typical store layout order for efficient shopping
        typical_store_order = [
            'Produce',
            'Dairy & Eggs',
            'Meat & Seafood',
            'Pantry & Dry Goods',
            'Beverages',
            'Frozen Foods',
            'Miscellaneous'
        ]
        
        route = []
        for section in typical_store_order:
            if section in organized_list and organized_list[section]:
                route.append(section)
        
        # Add any remaining sections not in the typical order
        for section in organized_list:
            if section not in route and organized_list[section]:
                route.append(section)
        
        return route
    
    def _identify_bulk_opportunities(self, ingredients_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify opportunities for bulk purchases to save money."""
        bulk_opportunities = []
        
        # Define bulk thresholds and savings
        bulk_thresholds = {
            'rice': {'threshold': 2, 'unit': 'kg', 'savings_percent': 15},
            'pasta': {'threshold': 1, 'unit': 'kg', 'savings_percent': 12},
            'chicken': {'threshold': 2, 'unit': 'kg', 'savings_percent': 10},
            'ground beef': {'threshold': 1, 'unit': 'kg', 'savings_percent': 8},
            'flour': {'threshold': 2, 'unit': 'kg', 'savings_percent': 20},
            'oil': {'threshold': 1, 'unit': 'liter', 'savings_percent': 15}
        }
        
        for item in ingredients_list:
            name_lower = item['name'].lower()
            
            # Check if item qualifies for bulk purchase
            for bulk_item, bulk_info in bulk_thresholds.items():
                if bulk_item in name_lower:
                    threshold_qty = bulk_info['threshold']
                    bulk_unit = bulk_info['unit']
                    
                    # Convert quantity to bulk unit if needed
                    item_qty_in_bulk_unit = self._convert_quantity(
                        item['quantity'], item['unit'], bulk_unit
                    )
                    
                    if item_qty_in_bulk_unit >= threshold_qty:
                        estimated_savings = item['estimated_price'] * (bulk_info['savings_percent'] / 100)
                        
                        bulk_opportunities.append({
                            'item_name': item['name'],
                            'current_quantity': item['quantity'],
                            'current_unit': item['unit'],
                            'bulk_quantity': threshold_qty,
                            'bulk_unit': bulk_unit,
                            'estimated_savings': round(estimated_savings, 2),
                            'savings_percent': bulk_info['savings_percent'],
                            'recommendation': f"Consider buying {threshold_qty} {bulk_unit} for {bulk_info['savings_percent']}% savings"
                        })
                        break
        
        return bulk_opportunities
    
    def _estimate_item_price(self, name: str, quantity: float, unit: str) -> float:
        """Estimate price for an item based on name, quantity, and unit."""
        # Basic price estimation - in a real implementation, this would use price databases
        base_prices = {
            'chicken': 8.99,  # per kg
            'beef': 12.99,    # per kg
            'pork': 7.99,     # per kg
            'salmon': 15.99,  # per kg
            'rice': 2.99,     # per kg
            'pasta': 1.99,    # per kg
            'bread': 2.99,    # per loaf
            'milk': 3.49,     # per liter
            'eggs': 3.99,     # per dozen
            'cheese': 6.99,   # per kg
            'tomato': 3.99,   # per kg
            'onion': 2.49,    # per kg
            'potato': 1.99,   # per kg
            'apple': 4.99,    # per kg
            'banana': 2.99,   # per kg
        }
        
        name_lower = name.lower()
        estimated_price = 2.99  # Default price
        
        # Find matching price
        for item_name, price in base_prices.items():
            if item_name in name_lower:
                estimated_price = price
                break
        
        # Adjust for quantity and unit
        if unit.lower() in ['kg', 'kilogram', 'liter', 'litre']:
            return estimated_price * quantity
        elif unit.lower() in ['gram', 'g', 'ml']:
            return estimated_price * (quantity / 1000)
        elif unit.lower() in ['pound', 'lb']:
            return estimated_price * (quantity * 0.453592)  # Convert lbs to kg
        else:
            # For pieces, assume reasonable portion sizes
            portion_multiplier = max(0.1, quantity / 10)  # Scale based on quantity
            return estimated_price * portion_multiplier
    
    def _estimate_total_cost(self, ingredients_list: List[Dict[str, Any]], 
                           preferences: Dict[str, Any]) -> float:
        """Estimate total cost of grocery list."""
        total_cost = sum(item.get('estimated_price', 0) for item in ingredients_list)
        
        # Apply any budget considerations
        budget = preferences.get('budget')
        if budget and total_cost > budget:
            # Could suggest cost-saving alternatives here
            pass
        
        return round(total_cost, 2)
    
    def _estimate_shopping_time(self, ingredients_list: List[Dict[str, Any]], 
                              preferences: Dict[str, Any]) -> str:
        """Estimate shopping time based on list size and preferences."""
        base_time = 20  # Base shopping time in minutes
        
        # Add time per item
        time_per_item = 1.5  # minutes per item
        item_time = len(ingredients_list) * time_per_item
        
        # Add time for store navigation
        navigation_time = 10
        
        # Add time for checkout
        checkout_time = 5
        
        total_minutes = base_time + item_time + navigation_time + checkout_time
        
        # Adjust based on preferences
        if preferences.get('store_familiarity') == 'high':
            total_minutes *= 0.8  # 20% faster if familiar with store
        elif preferences.get('store_familiarity') == 'low':
            total_minutes *= 1.3  # 30% longer if unfamiliar
        
        if preferences.get('shopping_experience') == 'expert':
            total_minutes *= 0.9  # 10% faster for experienced shoppers
        elif preferences.get('shopping_experience') == 'beginner':
            total_minutes *= 1.2  # 20% longer for beginners
        
        total_minutes = round(total_minutes)
        
        if total_minutes < 60:
            return f"{total_minutes} minutes"
        else:
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours}h {minutes}m"
    
    def _generate_shopping_tips(self, organized_list: Dict[str, List[Dict[str, Any]]], 
                              preferences: Dict[str, Any]) -> List[str]:
        """Generate helpful shopping tips based on the list and preferences."""
        tips = []
        
        # General tips
        tips.append("Start with produce and end with frozen items to maintain freshness")
        
        # Section-specific tips
        if 'Produce' in organized_list:
            tips.append("Check produce for ripeness and quality before purchasing")
        
        if 'Meat & Seafood' in organized_list:
            tips.append("Ask the butcher for recommendations and check sell-by dates")
        
        if 'Frozen Foods' in organized_list:
            tips.append("Shop frozen items last and transport in insulated bags")
        
        # Budget tips
        budget = preferences.get('budget')
        if budget:
            tips.append(f"Your estimated total is close to your ${budget} budget - consider generic brands for savings")
        
        # Store-specific tips
        preferred_store = preferences.get('preferred_store')
        if preferred_store:
            tips.append(f"Check {preferred_store}'s weekly deals and loyalty program discounts")
        
        # Efficiency tips
        if len(organized_list) > 5:
            tips.append("Use a shopping cart instead of a basket for easier navigation")
        
        return tips 