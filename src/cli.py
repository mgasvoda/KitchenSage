"""
KitchenCrew Chat CLI - Natural Language Interface for AI Cooking Assistant

This CLI provides a conversational interface where users can interact with
the KitchenCrew AI agents using natural language commands.
"""

import click
import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich.markdown import Markdown

from src.crew import KitchenCrew
from src.models.recipe import Recipe
from src.models.meal_plan import MealPlan


class CommandParser:
    """
    Natural language command parser that routes user input to appropriate agents.
    """
    
    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        
        # Command patterns for different agent capabilities
        # Note: Order matters! More specific patterns should come first
        self.patterns = {
            'search_stored_recipes': [
                r'what.*recipes?.*(?:do\s+i\s+have|available|stored|saved|in.*database)',
                r'show.*my.*recipes?',
                r'list.*my.*recipes?',
                r'browse.*my.*recipes?',
                r'search.*my.*recipes?',
                r'what.*(?:recipes?|dishes?).*(?:can\s+i\s+make|available).*(?:from|with).*(?:my|stored|saved)',
                r'recipes?.*(?:i\s+have|stored|saved|available)'
            ],
            'discover_new_recipes': [
                r'find.*new.*recipes?',
                r'discover.*new.*recipes?',
                r'search.*(?:online|web|internet).*recipes?',
                r'look.*for.*new.*recipes?',
                r'find.*recipes?.*online',
                r'get.*new.*recipe.*ideas',
                r'explore.*new.*recipes?',
                r'discover.*recipes?.*online'
            ],
            'find_recipes': [
                r'find.*recipes?',
                r'search.*recipes?',
                r'look.*for.*recipes?',
                r'discover.*recipes?',
                r'show.*me.*recipes?'
            ],
            'create_meal_plan': [
                r'create.*meal.*plan',
                r'build.*meal.*plan',
                r'make.*meal.*plan',
                r'plan.*meals?',
                r'weekly.*plan',
                r'meal.*planning'
            ],
            'generate_grocery_list': [
                r'grocery.*list',
                r'shopping.*list',
                r'generate.*list',
                r'create.*shopping',
                r'what.*to.*buy'
            ],
            'add_recipe': [
                r'add.*recipe',
                r'save.*recipe',
                r'store.*recipe',
                r'new.*recipe',
                r'create.*recipe'
            ],
            'get_suggestions': [
                r'suggest.*recipes?',
                r'what.*can.*i.*make',
                r'recipe.*suggestions?',
                r'ideas.*for.*cooking',
                r'recommendations?'
            ]
        }
        
        # Extraction patterns for parameters
        self.param_patterns = {
            'cuisine': r'(italian|mexican|chinese|indian|french|thai|japanese|mediterranean|american|greek|spanish|korean|vietnamese)',
            'dietary': r'(vegetarian|vegan|gluten.?free|dairy.?free|keto|paleo|low.?carb|halal|kosher)',
            'time': r'(\d+)\s*(minutes?|mins?|hours?|hrs?)',
            'days': r'(\d+)\s*(days?|day)',
            'people': r'(\d+)\s*(people|persons?|servings?)',
            'budget': r'(?:with\s+a\s+)?\$(\d+(?:\.\d{2})?)|(\d+)\s*dollars?',
            'ingredients': r'(?:with|using|have|got|make\s+with)\s+([^.!?]+?)(?:\?|$)',
            'vegetables': r'(vegetables?|veggies?|veggie|greens?|salad|heavy\s+on\s+vegetables?)',
            'meal_type': r'(breakfast|lunch|dinner|snack|appetizer|dessert)',
            'cooking_style': r'(light|heavy|hearty|fresh|crispy|creamy|spicy|mild)',
            'preparation': r'(quick|fast|easy|simple|slow|complex|advanced)'
        }
    
    def parse_command(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse natural language input and extract command type and parameters.
        
        Args:
            user_input: User's natural language command
            
        Returns:
            Tuple of (command_type, parameters)
        """
        user_input = user_input.lower().strip()
        
        # Determine command type
        command_type = self._identify_command_type(user_input)
        
        # Extract parameters based on command type
        parameters = self._extract_parameters(user_input, command_type)
        
        self.logger.info(f"Parsed command: {command_type} with params: {parameters}")
        return command_type, parameters
    
    def _identify_command_type(self, user_input: str) -> str:
        """Identify the type of command from user input."""
        for command_type, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    return command_type
        
        # Default to recipe search if unclear
        return 'find_recipes'
    
    def _extract_parameters(self, user_input: str, command_type: str) -> Dict[str, Any]:
        """Extract parameters from user input based on command type."""
        params = {}
        
        # Extract cuisine
        cuisine_match = re.search(self.param_patterns['cuisine'], user_input, re.IGNORECASE)
        if cuisine_match:
            params['cuisine'] = cuisine_match.group(1)
        
        # Extract dietary restrictions
        dietary_matches = re.findall(self.param_patterns['dietary'], user_input, re.IGNORECASE)
        if dietary_matches:
            params['dietary_restrictions'] = dietary_matches
        
        # Extract time constraints
        time_match = re.search(self.param_patterns['time'], user_input, re.IGNORECASE)
        if time_match:
            time_value = int(time_match.group(1))
            time_unit = time_match.group(2)
            if 'hour' in time_unit:
                time_value *= 60
            params['max_prep_time'] = time_value
        
        # Extract number of days (for meal planning)
        if command_type == 'create_meal_plan':
            days_match = re.search(self.param_patterns['days'], user_input, re.IGNORECASE)
            if days_match:
                params['days'] = int(days_match.group(1))
            elif 'week' in user_input:
                params['days'] = 7
            elif 'month' in user_input:
                params['days'] = 30
            else:
                params['days'] = 7  # Default to 1 week
        
        # Extract number of people
        people_match = re.search(self.param_patterns['people'], user_input, re.IGNORECASE)
        if people_match:
            params['people'] = int(people_match.group(1))
        
        # Extract budget
        budget_match = re.search(self.param_patterns['budget'], user_input, re.IGNORECASE)
        if budget_match:
            # Handle both $150 and "150 dollars" formats
            if budget_match.group(1):  # $150 format
                params['budget'] = float(budget_match.group(1))
            elif budget_match.group(2):  # 150 dollars format
                params['budget'] = float(budget_match.group(2))
        
        # Extract ingredients
        ingredients_match = re.search(self.param_patterns['ingredients'], user_input, re.IGNORECASE)
        if ingredients_match:
            ingredients_text = ingredients_match.group(1)
            # Split by common separators and clean up
            ingredients = []
            # Handle "and" as a separator
            for part in re.split(r'\s+and\s+', ingredients_text):
                # Further split by commas
                for ingredient in re.split(r',', part):
                    ingredient = ingredient.strip()
                    if ingredient and not ingredient.lower() in ['a', 'the', 'some']:
                        ingredients.append(ingredient)
            if ingredients:
                params['ingredients'] = ingredients
        
        # Extract vegetable preference
        vegetables_match = re.search(self.param_patterns['vegetables'], user_input, re.IGNORECASE)
        if vegetables_match:
            params['vegetable_focused'] = True
            # Add to dietary restrictions if not already present
            if 'dietary_restrictions' not in params:
                params['dietary_restrictions'] = []
            if 'vegetarian' not in [d.lower() for d in params['dietary_restrictions']]:
                params['dietary_restrictions'].append('vegetable-heavy')
        
        # Extract meal type
        meal_type_match = re.search(self.param_patterns['meal_type'], user_input, re.IGNORECASE)
        if meal_type_match:
            params['meal_type'] = meal_type_match.group(1)
        
        # Extract cooking style
        cooking_style_match = re.search(self.param_patterns['cooking_style'], user_input, re.IGNORECASE)
        if cooking_style_match:
            params['cooking_style'] = cooking_style_match.group(1)
        
        # Extract preparation style
        preparation_match = re.search(self.param_patterns['preparation'], user_input, re.IGNORECASE)
        if preparation_match:
            prep_style = preparation_match.group(1)
            if prep_style.lower() in ['quick', 'fast', 'easy', 'simple']:
                if 'max_prep_time' not in params:
                    params['max_prep_time'] = 30  # 30 minutes for quick recipes
                params['preparation_style'] = prep_style
        
        # Handle quick/fast keywords (legacy support)
        if re.search(r'\b(quick|fast|easy|simple)\b', user_input, re.IGNORECASE):
            if 'max_prep_time' not in params:
                params['max_prep_time'] = 30  # 30 minutes for quick recipes
        
        # Build a comprehensive search query for better context
        search_terms = []
        if params.get('meal_type'):
            search_terms.append(params['meal_type'])
        if params.get('cooking_style'):
            search_terms.append(params['cooking_style'])
        if params.get('vegetable_focused'):
            search_terms.append('vegetable')
        if params.get('cuisine'):
            search_terms.append(params['cuisine'])
        if params.get('max_prep_time') and params['max_prep_time'] <= 30:
            search_terms.append('quick')
        
        if search_terms:
            params['search_query'] = ' '.join(search_terms) + ' recipes'
        
        return params


class KitchenCrewCLI:
    """
    Main CLI class that provides a chat interface for the KitchenCrew system.
    """
    
    def __init__(self):
        self.console = Console()
        self.parser = CommandParser()
        self.crew = KitchenCrew()
        self.conversation_history = []
        self.logger = logging.getLogger(__name__)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def start_chat(self):
        """Start the interactive chat session."""
        self.console.print(Panel.fit(
            "[bold blue]🍳 Welcome to KitchenCrew AI Assistant! 🍳[/bold blue]\n\n"
            "I'm your AI-powered cooking companion. You can ask me to:\n"
            "• Find recipes: 'find quick mediterranean recipes'\n"
            "• Plan meals: 'create a meal plan for this week'\n"
            "• Generate grocery lists: 'make a shopping list for my meal plan'\n"
            "• Get suggestions: 'what can I make with chicken and rice?'\n"
            "• Add recipes: 'save this new pasta recipe'\n\n"
            "Type 'help' for more examples or 'quit' to exit.",
            title="KitchenCrew Chat",
            border_style="blue"
        ))
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold green]You[/bold green]")
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    self.console.print("[yellow]Thanks for using KitchenCrew! Happy cooking! 👨‍🍳[/yellow]")
                    break
                
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                if user_input.lower() == 'history':
                    self._show_history()
                    continue
                
                # Process the command
                self._process_command(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
            except Exception as e:
                self.logger.error(f"Error in chat loop: {e}")
                self.console.print(f"[red]Sorry, I encountered an error: {e}[/red]")
    
    def _process_command(self, user_input: str):
        """Process a user command and return the response."""
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'user_input': user_input,
            'response': None
        })
        
        try:
            # Parse the command
            command_type, parameters = self.parser.parse_command(user_input)
            
            # Show what we understood
            self._show_understanding(command_type, parameters)
            
            # Execute the command
            with self.console.status("[bold blue]🤖 AI agents are working...", spinner="dots"):
                result = self._execute_command(command_type, parameters)
            
            # Display the result
            self._display_result(result, command_type)
            
            # Update conversation history
            self.conversation_history[-1]['response'] = result
            
        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
            self.console.print(f"[red]I'm sorry, I couldn't process that request: {e}[/red]")
    
    def _show_understanding(self, command_type: str, parameters: Dict[str, Any]):
        """Show what the system understood from the user's input."""
        understanding = f"[dim]I understand you want to: {command_type.replace('_', ' ')}"
        if parameters:
            understanding += f" with: {', '.join(f'{k}={v}' for k, v in parameters.items())}"
        understanding += "[/dim]"
        self.console.print(understanding)
    
    def _execute_command(self, command_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the parsed command using the appropriate CrewAI agents."""
        try:
            if command_type == 'find_recipes':
                # Filter parameters to only include those accepted by find_recipes
                valid_params = {
                    k: v for k, v in parameters.items() 
                    if k in ['cuisine', 'dietary_restrictions', 'ingredients', 'max_prep_time']
                }
                return self.crew.find_recipes(**valid_params)
            
            elif command_type == 'search_stored_recipes':
                # Filter parameters for search_stored_recipes
                valid_params = {
                    k: v for k, v in parameters.items() 
                    if k in ['cuisine', 'dietary_restrictions', 'ingredients', 'max_prep_time']
                }
                return self.crew.search_stored_recipes(**valid_params)
            
            elif command_type == 'discover_new_recipes':
                # Filter parameters for discover_new_recipes
                valid_params = {
                    k: v for k, v in parameters.items() 
                    if k in ['cuisine', 'dietary_restrictions', 'ingredients', 'max_prep_time']
                }
                return self.crew.discover_new_recipes(**valid_params)
            
            elif command_type == 'create_meal_plan':
                # Filter parameters for create_meal_plan
                valid_params = {
                    k: v for k, v in parameters.items() 
                    if k in ['days', 'people', 'dietary_restrictions', 'budget']
                }
                return self.crew.create_meal_plan(**valid_params)
            
            elif command_type == 'generate_grocery_list':
                # For grocery list, we need a meal plan ID
                # This is a simplified implementation - in practice, you'd want to
                # let users select from existing meal plans
                meal_plan_id = parameters.get('meal_plan_id', 1)  # Default to 1
                return self.crew.generate_grocery_list(meal_plan_id)
            
            elif command_type == 'add_recipe':
                # For adding recipes, we'd need to collect recipe data
                # This is a placeholder - you'd want to implement a recipe input flow
                recipe_data = parameters.get('recipe_data', {})
                return self.crew.add_recipe(recipe_data)
            
            elif command_type == 'get_suggestions':
                ingredients = parameters.get('ingredients', [])
                return self.crew.get_recipe_suggestions(ingredients)
            
            else:
                return {"status": "error", "message": f"Unknown command type: {command_type}"}
                
        except Exception as e:
            self.logger.error(f"Error executing command {command_type}: {e}")
            return {"status": "error", "message": str(e)}
    
    def _display_result(self, result: Dict[str, Any], command_type: str):
        """Display the result from the AI agents in a user-friendly format."""
        if isinstance(result, str):
            # If result is a string (from CrewAI), display it as markdown
            self.console.print(Panel(
                Markdown(result),
                title="🤖 KitchenCrew Assistant",
                border_style="green"
            ))
        elif isinstance(result, dict):
            if result.get('status') == 'error':
                self.console.print(f"[red]❌ Error: {result.get('message', 'Unknown error')}[/red]")
            else:
                # Format based on command type
                if command_type == 'find_recipes':
                    self._display_recipes(result, "🍽️ Recipe Results")
                elif command_type == 'search_stored_recipes':
                    self._display_recipes(result, "📚 Your Stored Recipes")
                elif command_type == 'discover_new_recipes':
                    self._display_recipes(result, "🌐 New Recipes Discovered")
                elif command_type == 'create_meal_plan':
                    self._display_meal_plan(result)
                elif command_type == 'generate_grocery_list':
                    self._display_grocery_list(result)
                else:
                    # Generic display
                    self.console.print(Panel(
                        json.dumps(result, indent=2),
                        title="🤖 Result",
                        border_style="green"
                    ))
        else:
            self.console.print(Panel(
                str(result),
                title="🤖 KitchenCrew Assistant",
                border_style="green"
            ))
    
    def _display_recipes(self, result: Any, title: str = "🍽️ Recipe Results"):
        """Display recipe search results with appropriate title."""
        self.console.print(Panel(
            str(result),
            title=title,
            border_style="green"
        ))
    
    def _display_meal_plan(self, result: Any):
        """Display meal plan results."""
        self.console.print(Panel(
            str(result),
            title="📅 Meal Plan",
            border_style="blue"
        ))
    
    def _display_grocery_list(self, result: Any):
        """Display grocery list results."""
        self.console.print(Panel(
            str(result),
            title="🛒 Grocery List",
            border_style="yellow"
        ))
    
    def _show_help(self):
        """Display help information."""
        help_text = """
[bold blue]KitchenCrew Commands & Examples:[/bold blue]

[bold green]🔍 Finding Recipes:[/bold green]
• "find quick italian recipes" - General recipe search
• "search for vegetarian meals under 30 minutes"
• "show me gluten-free mediterranean dishes"

[bold green]📚 Searching Your Stored Recipes:[/bold green]
• "what recipes do I have available?"
• "show my italian recipes"
• "list my vegetarian recipes"
• "what can I make from my stored recipes?"
• "browse my saved recipes"

[bold green]🌐 Discovering New Recipes Online:[/bold green]
• "find new italian recipes"
• "discover new vegetarian recipes online"
• "search the web for gluten-free recipes"
• "explore new recipe ideas"
• "get new recipe suggestions"

[bold green]📅 Meal Planning:[/bold green]
• "create a meal plan for this week"
• "build a 5-day meal plan for 4 people"
• "plan meals for 2 weeks with a $200 budget"
• "make a vegetarian meal plan"

[bold green]🛒 Grocery Lists:[/bold green]
• "generate a grocery list for my meal plan"
• "create a shopping list"
• "what do I need to buy?"

[bold green]💡 Recipe Suggestions:[/bold green]
• "what can I make with tomatoes and pasta?"
• "suggest recipes using chicken and vegetables"
• "recipe ideas for dinner tonight"

[bold green]📝 Adding Recipes:[/bold green]
• "add my grandmother's pasta recipe"
• "save this new recipe I found"

[bold green]🔧 Other Commands:[/bold green]
• "help" - Show this help
• "history" - Show conversation history
• "quit" or "exit" - Exit the chat
        """
        
        self.console.print(Panel(help_text, title="Help", border_style="cyan"))
    
    def _show_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            self.console.print("[yellow]No conversation history yet.[/yellow]")
            return
        
        table = Table(title="Conversation History")
        table.add_column("Time", style="cyan")
        table.add_column("Your Message", style="green")
        table.add_column("Response", style="blue")
        
        for entry in self.conversation_history[-10:]:  # Show last 10 entries
            time_str = entry['timestamp'].strftime("%H:%M:%S")
            user_msg = entry['user_input'][:50] + "..." if len(entry['user_input']) > 50 else entry['user_input']
            response = "✅ Completed" if entry['response'] else "❌ Failed"
            table.add_row(time_str, user_msg, response)
        
        self.console.print(table)


@click.group()
def cli():
    """KitchenCrew AI Cooking Assistant"""
    pass


@cli.command()
def chat():
    """Start the interactive chat interface with KitchenCrew AI agents."""
    kitchen_cli = KitchenCrewCLI()
    kitchen_cli.start_chat()


@cli.command()
@click.argument('command', required=True)
def ask(command):
    """Ask a single question to KitchenCrew AI agents."""
    kitchen_cli = KitchenCrewCLI()
    kitchen_cli._process_command(command)


if __name__ == "__main__":
    cli()
