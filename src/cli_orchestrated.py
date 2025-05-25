"""
KitchenCrew Orchestrated CLI - AI Agent-Based Natural Language Interface

This CLI uses an AI orchestrator agent to understand user queries and coordinate
with specialized agents, replacing the rule-based parsing approach.
"""

import click
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich.markdown import Markdown

from crewai import Crew, Process
from src.agents.orchestrator import OrchestratorAgent
from src.agents.recipe_manager import RecipeManagerAgent
from src.agents.meal_planner import MealPlannerAgent
from src.agents.recipe_scout import RecipeScoutAgent
from src.agents.grocery_list import GroceryListAgent
from src.tasks.orchestrator_tasks import OrchestratorTasks
from src.crew import KitchenCrew


def extract_crew_output(result: Any) -> str:
    """Extract the actual result text from a CrewOutput object or return as string."""
    if hasattr(result, 'raw'):
        return result.raw
    elif hasattr(result, 'result'):
        return result.result
    else:
        return str(result)


class OrchestratedKitchenCrewCLI:
    """
    AI-orchestrated CLI that uses natural language understanding to route user queries.
    """
    
    def __init__(self):
        self.console = Console()
        self.conversation_history = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize the orchestrator agent and tasks
        self.orchestrator_agent = OrchestratorAgent()
        self.orchestrator_tasks = OrchestratorTasks()
        
        # Initialize other agents for coordination
        self.recipe_manager = RecipeManagerAgent()
        self.meal_planner = MealPlannerAgent()
        self.recipe_scout = RecipeScoutAgent()
        self.grocery_list_agent = GroceryListAgent()
        
        # Keep the existing KitchenCrew for executing specialized tasks
        self.kitchen_crew = KitchenCrew()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def start_chat(self):
        """Start the interactive chat session."""
        # Show telemetry status
        from src.utils.telemetry import is_tracing_enabled
        
        tracing_status = "🔭 Phoenix tracing: " + ("✅ Active" if is_tracing_enabled() else "❌ Disabled")
        
        self.console.print(Panel.fit(
            "[bold blue]🍳 Welcome to KitchenCrew AI Assistant! 🍳[/bold blue]\n\n"
            "I'm your AI-powered cooking companion with natural language understanding.\n"
            "Just tell me what you want in plain English:\n\n"
            "• 'I want to make something quick with chicken and rice'\n"
            "• 'Plan my meals for next week, I'm vegetarian'\n"
            "• 'What can I cook for dinner tonight?'\n"
            "• 'I need a grocery list for my meal plan'\n"
            "• 'Find me some healthy breakfast ideas'\n\n"
            f"{tracing_status}\n\n"
            "Type 'help' for more examples, 'telemetry' for tracing info, or 'quit' to exit.",
            title="KitchenCrew AI Chat",
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
                
                if user_input.lower() == 'telemetry':
                    self._show_telemetry_status()
                    continue
                
                # Process the command using the orchestrator
                self._process_with_orchestrator(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
            except Exception as e:
                self.logger.error(f"Error in chat loop: {e}")
                self.console.print(f"[red]Sorry, I encountered an error: {e}[/red]")
    
    def _process_with_orchestrator(self, user_input: str):
        """Process user input using the orchestrator agent."""
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'user_input': user_input,
            'response': None
        })
        
        try:
            # Get conversation context from recent history
            context = self._get_conversation_context()
            
            with self.console.status("[bold blue]🤖 Understanding your request...", spinner="dots"):
                # Step 1: Parse the user query
                parsed_result = self._parse_user_query(user_input, context)
            
            # Check if we need clarification
            if self._needs_clarification(parsed_result):
                self._handle_clarification(user_input, parsed_result)
                return
            
            # Step 2: Execute the request using appropriate agents
            with self.console.status("[bold blue]🤖 AI agents are working...", spinner="dots"):
                result = self._execute_parsed_request(parsed_result)
            
            # Display the result
            self._display_result(result)
            
            # Update conversation history
            self.conversation_history[-1]['response'] = result
            
        except Exception as e:
            self.logger.error(f"Error processing with orchestrator: {e}")
            self.console.print(f"[red]I'm sorry, I couldn't process that request: {e}[/red]")
    
    def _parse_user_query(self, user_input: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Use the orchestrator agent to parse the user query."""
        # Create parsing task
        parse_task = self.orchestrator_tasks.parse_user_query_task(user_input, context)
        parse_task.agent = self.orchestrator_agent.agent
        
        # Create a crew with just the orchestrator for parsing
        parse_crew = Crew(
            agents=[self.orchestrator_agent.agent],
            tasks=[parse_task],
            process=Process.sequential,
            verbose=False  # Keep parsing quiet
        )
        
        # Execute the parsing
        result = parse_crew.kickoff()
        
        # Handle CrewOutput object
        try:
            # Extract the actual result from CrewOutput
            result_text = extract_crew_output(result)
            
            # Try to parse JSON from the result text
            if isinstance(result_text, str):
                # Extract JSON from the result if it's embedded in text
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group())
                else:
                    # Fallback: create a basic structure
                    parsed_data = {
                        "intent": "find_recipes",
                        "confidence": "medium",
                        "parameters": {},
                        "agents_needed": ["recipe_scout"],
                        "clarification_needed": False,
                        "clarifying_questions": [],
                        "reasoning": result_text
                    }
            else:
                # If it's already a dict, use it directly
                parsed_data = result_text if isinstance(result_text, dict) else {}
                
            return parsed_data
        except (json.JSONDecodeError, AttributeError) as e:
            self.logger.warning(f"Could not parse orchestrator result as JSON: {e}")
            self.logger.warning(f"Result type: {type(result)}, Result: {result}")
            # Return a fallback structure
            return {
                "intent": "find_recipes",
                "confidence": "low",
                "parameters": {"original_query": user_input},
                "agents_needed": ["recipe_scout"],
                "clarification_needed": False,
                "clarifying_questions": [],
                "reasoning": f"Fallback parsing due to JSON error: {str(result)}"
            }
    
    def _needs_clarification(self, parsed_result: Dict[str, Any]) -> bool:
        """Check if the parsed result indicates clarification is needed."""
        return (
            parsed_result.get("clarification_needed", False) or
            parsed_result.get("confidence", "high") == "low" or
            len(parsed_result.get("clarifying_questions", [])) > 0
        )
    
    def _handle_clarification(self, user_input: str, parsed_result: Dict[str, Any]):
        """Handle requests that need clarification."""
        clarifying_questions = parsed_result.get("clarifying_questions", [])
        
        # Create clarification task
        clarify_task = self.orchestrator_tasks.clarify_user_intent_task(user_input, clarifying_questions)
        clarify_task.agent = self.orchestrator_agent.agent
        
        # Create a crew for clarification
        clarify_crew = Crew(
            agents=[self.orchestrator_agent.agent],
            tasks=[clarify_task],
            process=Process.sequential,
            verbose=False
        )
        
        # Execute clarification
        clarification_response = clarify_crew.kickoff()
        
        # Extract the actual response from CrewOutput
        response_text = extract_crew_output(clarification_response)
        
        # Display the clarification request
        self.console.print(Panel(
            response_text,
            title="🤔 I need a bit more information",
            border_style="yellow"
        ))
    
    def _execute_parsed_request(self, parsed_result: Dict[str, Any]) -> Any:
        """Execute the parsed request using the appropriate KitchenCrew methods."""
        intent = parsed_result.get("intent", "find_recipes")
        parameters = parsed_result.get("parameters", {})
        
        # Clean up parameters - remove null values and convert to appropriate types
        clean_params = {}
        for key, value in parameters.items():
            if value is not None and value != "null" and value != "":
                if key == "dietary_restrictions" and isinstance(value, str):
                    clean_params[key] = [value]
                elif key == "ingredients" and isinstance(value, str):
                    clean_params[key] = [value]
                else:
                    clean_params[key] = value
        
        # Route to appropriate KitchenCrew method based on intent
        try:
            if intent == "find_recipes" or intent == "recipe_search":
                return self.kitchen_crew.find_recipes(**clean_params)
            elif intent == "search_stored_recipes":
                return self.kitchen_crew.search_stored_recipes(**clean_params)
            elif intent == "discover_new_recipes":
                return self.kitchen_crew.discover_new_recipes(**clean_params)
            elif intent == "create_meal_plan" or intent == "meal_planning":
                return self.kitchen_crew.create_meal_plan(**clean_params)
            elif intent == "generate_grocery_list" or intent == "grocery_list":
                meal_plan_id = clean_params.get('meal_plan_id', 1)
                return self.kitchen_crew.generate_grocery_list(meal_plan_id)
            elif intent == "add_recipe" or intent == "recipe_management":
                recipe_data = clean_params.get('recipe_data', clean_params)
                return self.kitchen_crew.add_recipe(recipe_data)
            elif intent == "get_suggestions" or intent == "recipe_suggestions":
                ingredients = clean_params.get('ingredients', [])
                return self.kitchen_crew.get_recipe_suggestions(ingredients)
            else:
                # Default to recipe search
                return self.kitchen_crew.find_recipes(**clean_params)
                
        except Exception as e:
            self.logger.error(f"Error executing {intent}: {e}")
            return f"I encountered an error while {intent.replace('_', ' ')}: {str(e)}"
    
    def _get_conversation_context(self) -> Optional[str]:
        """Get recent conversation context for better understanding."""
        if len(self.conversation_history) < 2:
            return None
        
        # Get last 3 interactions for context
        recent_history = self.conversation_history[-3:]
        context_parts = []
        
        for entry in recent_history:
            context_parts.append(f"User: {entry['user_input']}")
            if entry['response']:
                # Truncate long responses
                response_str = str(entry['response'])
                if len(response_str) > 200:
                    response_str = response_str[:200] + "..."
                context_parts.append(f"Assistant: {response_str}")
        
        return "\n".join(context_parts)
    
    def _display_result(self, result: Any):
        """Display the result from the AI agents."""
        # Extract the actual result from CrewOutput if needed
        result_text = extract_crew_output(result)
        
        if isinstance(result_text, str):
            # If result is a string (from CrewAI), display it as markdown
            self.console.print(Panel(
                Markdown(result_text),
                title="🤖 KitchenCrew Assistant",
                border_style="green"
            ))
        else:
            # For other types, convert to string and display
            self.console.print(Panel(
                str(result_text),
                title="🤖 KitchenCrew Assistant",
                border_style="green"
            ))
    
    def _show_help(self):
        """Display help information."""
        help_text = """
[bold blue]KitchenCrew AI Assistant - Natural Language Examples:[/bold blue]

[bold green]🔍 Finding Recipes:[/bold green]
• "I want to make something quick with chicken"
• "Find me healthy vegetarian dinner ideas"
• "What can I cook with tomatoes and pasta?"
• "Show me easy breakfast recipes under 15 minutes"
• "I need gluten-free italian recipes"

[bold green]📅 Meal Planning:[/bold green]
• "Plan my meals for this week"
• "Create a 5-day meal plan for 2 people"
• "I need a vegetarian meal plan with a $100 budget"
• "Plan healthy meals for my family of 4"

[bold green]🛒 Grocery Lists:[/bold green]
• "Generate a grocery list for my meal plan"
• "What do I need to buy for this week's meals?"
• "Create a shopping list"

[bold green]💡 Recipe Suggestions:[/bold green]
• "What can I make with chicken, rice, and vegetables?"
• "Suggest dinner ideas for tonight"
• "I have eggs and cheese, what can I cook?"

[bold green]📝 Recipe Management:[/bold green]
• "Save this recipe I found"
• "Add my grandmother's pasta recipe"
• "Store this new recipe"

[bold green]🔧 Other Commands:[/bold green]
• "help" - Show this help
• "history" - Show conversation history
• "telemetry" - Show Phoenix tracing status
• "quit" or "exit" - Exit the chat

[bold yellow]💡 Tips:[/bold yellow]
• Speak naturally - the AI understands context and intent
• Be as specific or general as you like
• Ask follow-up questions to refine results
• The AI will ask for clarification if needed
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

    def _show_telemetry_status(self):
        """Show Phoenix telemetry configuration status."""
        from src.utils.telemetry import get_tracing_info, is_tracing_enabled
        
        console = Console()
        tracing_info = get_tracing_info()
        
        # Create status table
        table = Table(title="🔭 Phoenix Telemetry Status")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green" if tracing_info["enabled"] else "red")
        
        table.add_row("Tracing Enabled", "✅ Yes" if tracing_info["enabled"] else "❌ No")
        table.add_row("API Key Configured", "✅ Yes" if tracing_info["api_key_configured"] else "❌ No")
        table.add_row("Project Name", tracing_info["project_name"])
        table.add_row("Endpoint", tracing_info["endpoint"])
        
        console.print(table)
        
        if tracing_info["enabled"]:
            console.print("\n[green]✅ Phoenix tracing is active! Your CrewAI interactions will be traced.[/green]")
            console.print("[blue]📊 View your traces at: https://app.phoenix.arize.com[/blue]")
        else:
            console.print("\n[yellow]⚠️  Phoenix tracing is not enabled.[/yellow]")
            console.print("[blue]💡 To enable tracing:[/blue]")
            console.print("   1. Set your PHOENIX_API_KEY in the .env file")
            console.print("   2. Restart the application")
            console.print("   3. Get your API key from: https://app.phoenix.arize.com")


@click.group()
def cli():
    """KitchenCrew AI Cooking Assistant with Orchestrated Agents"""
    pass


@cli.command()
def chat():
    """Start the interactive AI-orchestrated chat interface."""
    kitchen_cli = OrchestratedKitchenCrewCLI()
    kitchen_cli.start_chat()


@cli.command()
@click.argument('command', required=True)
def ask(command):
    """Ask a single question to the AI-orchestrated KitchenCrew agents."""
    kitchen_cli = OrchestratedKitchenCrewCLI()
    kitchen_cli._process_with_orchestrator(command)


@cli.command()
def telemetry():
    """Show Phoenix telemetry configuration status."""
    from src.utils.telemetry import get_tracing_info, is_tracing_enabled
    
    console = Console()
    tracing_info = get_tracing_info()
    
    # Create status table
    table = Table(title="🔭 Phoenix Telemetry Status")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green" if tracing_info["enabled"] else "red")
    
    table.add_row("Tracing Enabled", "✅ Yes" if tracing_info["enabled"] else "❌ No")
    table.add_row("API Key Configured", "✅ Yes" if tracing_info["api_key_configured"] else "❌ No")
    table.add_row("Project Name", tracing_info["project_name"])
    table.add_row("Endpoint", tracing_info["endpoint"])
    
    console.print(table)
    
    if tracing_info["enabled"]:
        console.print("\n[green]✅ Phoenix tracing is active! Your CrewAI interactions will be traced.[/green]")
        console.print("[blue]📊 View your traces at: https://app.phoenix.arize.com[/blue]")
    else:
        console.print("\n[yellow]⚠️  Phoenix tracing is not enabled.[/yellow]")
        console.print("[blue]💡 To enable tracing:[/blue]")
        console.print("   1. Set your PHOENIX_API_KEY in the .env file")
        console.print("   2. Restart the application")
        console.print("   3. Get your API key from: https://app.phoenix.arize.com")


if __name__ == "__main__":
    cli() 