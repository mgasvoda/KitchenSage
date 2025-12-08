"""
Chat service - handles AI chat with streaming support.
"""

import logging
import asyncio
import json
from typing import Optional, List, Dict, Any, AsyncGenerator

from crewai import Crew, Process
from src.agents.orchestrator import OrchestratorAgent
from src.agents.recipe_manager import RecipeManagerAgent
from src.agents.meal_planner import MealPlannerAgent
from src.agents.recipe_scout import RecipeScoutAgent
from src.agents.grocery_list import GroceryListAgent
from src.tasks.orchestrator_tasks import OrchestratorTasks
from src.crew import KitchenCrew

logger = logging.getLogger(__name__)


def extract_crew_output(result: Any) -> str:
    """Extract the actual result text from a CrewOutput object or return as string."""
    if hasattr(result, 'raw'):
        return result.raw
    elif hasattr(result, 'result'):
        return result.result
    else:
        return str(result)


class ChatService:
    """
    Service layer for chat operations with streaming support.
    
    Handles natural language processing using AI agents and
    coordinates responses with real-time streaming.
    """
    
    def __init__(self):
        self._orchestrator_agent = None
        self._orchestrator_tasks = None
        self._kitchen_crew = None
    
    @property
    def orchestrator_agent(self) -> OrchestratorAgent:
        """Lazy initialization of orchestrator agent."""
        if self._orchestrator_agent is None:
            self._orchestrator_agent = OrchestratorAgent()
        return self._orchestrator_agent
    
    @property
    def orchestrator_tasks(self) -> OrchestratorTasks:
        """Lazy initialization of orchestrator tasks."""
        if self._orchestrator_tasks is None:
            self._orchestrator_tasks = OrchestratorTasks()
        return self._orchestrator_tasks
    
    @property
    def kitchen_crew(self) -> KitchenCrew:
        """Lazy initialization of kitchen crew."""
        if self._kitchen_crew is None:
            self._kitchen_crew = KitchenCrew()
        return self._kitchen_crew
    
    async def process_message_stream(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a chat message and stream the response.
        
        Args:
            message: User message
            history: Conversation history
            
        Yields:
            Chunks of the response with type information
        """
        try:
            # Yield thinking status
            yield {"type": "thinking", "content": "Understanding your request..."}
            
            # Parse the user query
            context = self._format_history(history) if history else None
            parsed_result = await asyncio.to_thread(
                self._parse_user_query, message, context
            )
            
            yield {"type": "thinking", "content": "Processing..."}
            
            # Check if clarification is needed
            if self._needs_clarification(parsed_result):
                clarification = parsed_result.get("clarifying_questions", [])
                if clarification:
                    yield {
                        "type": "complete",
                        "content": f"I need a bit more information:\n" + "\n".join(f"- {q}" for q in clarification),
                        "intent": "clarification",
                    }
                    return
            
            # Execute the request
            yield {"type": "thinking", "content": "Working on your request..."}
            
            result = await asyncio.to_thread(
                self._execute_parsed_request, parsed_result
            )
            
            # Extract the result text
            result_text = extract_crew_output(result)
            
            # Stream the result in chunks for a more dynamic feel
            words = result_text.split()
            chunk_size = 5  # Words per chunk
            
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i:i + chunk_size])
                yield {"type": "token", "content": chunk + " "}
                await asyncio.sleep(0.05)  # Small delay between chunks
            
            # Send completion
            yield {
                "type": "complete",
                "content": result_text,
                "intent": parsed_result.get("intent"),
            }
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}")
            yield {"type": "error", "content": str(e)}
    
    async def process_message(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a chat message synchronously.
        
        Args:
            message: User message
            history: Conversation history
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Parse the user query
            context = self._format_history(history) if history else None
            parsed_result = self._parse_user_query(message, context)
            
            # Check if clarification is needed
            if self._needs_clarification(parsed_result):
                clarification = parsed_result.get("clarifying_questions", [])
                return {
                    "status": "clarification_needed",
                    "response": "I need a bit more information:\n" + "\n".join(f"- {q}" for q in clarification),
                    "intent": "clarification",
                }
            
            # Execute the request
            result = self._execute_parsed_request(parsed_result)
            result_text = extract_crew_output(result)
            
            return {
                "status": "success",
                "response": result_text,
                "intent": parsed_result.get("intent"),
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for context."""
        if not history:
            return ""
        
        parts = []
        for entry in history[-5:]:  # Last 5 messages
            role = entry.get("role", "user").title()
            content = entry.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            parts.append(f"{role}: {content}")
        
        return "\n".join(parts)
    
    def _parse_user_query(self, message: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Use the orchestrator agent to parse the user query."""
        import re
        
        # Create parsing task
        parse_task = self.orchestrator_tasks.parse_user_query_task(message, context)
        parse_task.agent = self.orchestrator_agent.agent
        
        # Create a crew with just the orchestrator for parsing
        parse_crew = Crew(
            agents=[self.orchestrator_agent.agent],
            tasks=[parse_task],
            process=Process.sequential,
            verbose=False
        )
        
        # Execute the parsing
        result = parse_crew.kickoff()
        
        # Handle CrewOutput object
        try:
            result_text = extract_crew_output(result)
            
            if isinstance(result_text, str):
                # Extract JSON from the result if it's embedded in text
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    parsed_data = json.loads(json_match.group())
                else:
                    # Fallback: create a basic structure
                    parsed_data = {
                        "intent": "find_recipes",
                        "confidence": "medium",
                        "parameters": {"original_query": message},
                        "agents_needed": ["recipe_scout"],
                        "clarification_needed": False,
                        "clarifying_questions": [],
                        "reasoning": result_text
                    }
            else:
                parsed_data = result_text if isinstance(result_text, dict) else {}
                
            return parsed_data
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Could not parse orchestrator result as JSON: {e}")
            return {
                "intent": "find_recipes",
                "confidence": "low",
                "parameters": {"original_query": message},
                "agents_needed": ["recipe_scout"],
                "clarification_needed": False,
                "clarifying_questions": [],
            }
    
    def _needs_clarification(self, parsed_result: Dict[str, Any]) -> bool:
        """Check if the parsed result indicates clarification is needed."""
        return (
            parsed_result.get("clarification_needed", False) or
            parsed_result.get("confidence", "high") == "low" or
            len(parsed_result.get("clarifying_questions", [])) > 0
        )
    
    def _execute_parsed_request(self, parsed_result: Dict[str, Any]) -> Any:
        """Execute the parsed request using the appropriate KitchenCrew methods."""
        intent = parsed_result.get("intent", "find_recipes")
        parameters = parsed_result.get("parameters", {})
        
        # Clean up parameters
        clean_params = {}
        for key, value in parameters.items():
            if value is not None and value != "null" and value != "":
                if key == "dietary_restrictions" and isinstance(value, str):
                    clean_params[key] = [value]
                elif key == "ingredients" and isinstance(value, str):
                    clean_params[key] = [value]
                else:
                    clean_params[key] = value
        
        # Route to appropriate method
        try:
            if intent in ("find_recipes", "recipe_search"):
                return self.kitchen_crew.find_recipes(**clean_params)
            elif intent == "search_stored_recipes":
                return self.kitchen_crew.search_stored_recipes(**clean_params)
            elif intent == "discover_new_recipes":
                return self.kitchen_crew.discover_new_recipes(**clean_params)
            elif intent in ("create_meal_plan", "meal_planning"):
                return self.kitchen_crew.create_meal_plan(**clean_params)
            elif intent in ("generate_grocery_list", "grocery_list"):
                meal_plan_id = clean_params.get('meal_plan_id', 1)
                return self.kitchen_crew.generate_grocery_list(meal_plan_id)
            elif intent in ("add_recipe", "recipe_management"):
                recipe_data = clean_params.get('recipe_data', clean_params)
                return self.kitchen_crew.add_recipe(recipe_data)
            elif intent in ("get_suggestions", "recipe_suggestions"):
                ingredients = clean_params.get('ingredients', [])
                return self.kitchen_crew.get_recipe_suggestions(ingredients)
            else:
                return self.kitchen_crew.find_recipes(**clean_params)
                
        except Exception as e:
            logger.error(f"Error executing {intent}: {e}")
            return f"I encountered an error while {intent.replace('_', ' ')}: {str(e)}"

