"""
Orchestrator task definitions for CrewAI agents.
"""

from crewai import Task
from typing import Dict, Any, Optional


class OrchestratorTasks:
    """Task definitions for query orchestration and routing operations."""
    
    def parse_user_query_task(self, user_input: str, conversation_context: Optional[str] = None) -> Task:
        """
        Task to parse and understand a user's natural language query.
        
        Args:
            user_input: The user's natural language input
            conversation_context: Optional context from previous conversation
            
        Returns:
            CrewAI Task object
        """
        context_text = f"\n\nConversation context: {conversation_context}" if conversation_context else ""
        
        return Task(
            description=f"""
            Analyze the following user query and extract the intent and parameters:
            
            User Query: "{user_input}"{context_text}
            
            Your task is to:
            1. Understand what the user wants to accomplish
            2. Identify the primary intent (recipe search, meal planning, grocery list, etc.)
            3. Extract relevant parameters like:
               - Cuisine preferences (italian, mexican, etc.)
               - Dietary restrictions (vegetarian, gluten-free, etc.)
               - Time constraints (quick, under 30 minutes, etc.)
               - Number of people/servings
               - Available ingredients
               - Budget constraints
               - Meal types (breakfast, lunch, dinner)
               - Any other relevant cooking preferences
            4. Determine if additional clarification is needed from the user
            5. Identify which KitchenCrew agents should be involved
            
            Available KitchenCrew capabilities:
            - Recipe search (both stored recipes and new recipe discovery)
            - Meal planning (create weekly/monthly meal plans)
            - Grocery list generation (from meal plans)
            - Recipe management (add, store, organize recipes)
            - Recipe suggestions (based on available ingredients)
            
            If the query is ambiguous or missing critical information, identify what 
            clarifying questions should be asked.
            """,
            expected_output="""JSON object with:
            {
                "intent": "primary_action_needed",
                "confidence": "high/medium/low",
                "parameters": {
                    "cuisine": "extracted_cuisine_or_null",
                    "dietary_restrictions": ["list_of_restrictions"],
                    "ingredients": ["list_of_ingredients"],
                    "max_prep_time": "time_in_minutes_or_null",
                    "people": "number_of_people_or_null",
                    "budget": "budget_amount_or_null",
                    "meal_type": "breakfast/lunch/dinner/snack_or_null",
                    "days": "number_of_days_for_meal_plan_or_null"
                },
                "agents_needed": ["list_of_required_agents"],
                "clarification_needed": "true/false",
                "clarifying_questions": ["list_of_questions_if_needed"],
                "reasoning": "explanation_of_interpretation"
            }""",
            async_execution=False,
            context=[]
        )
    
    def route_to_agents_task(self, parsed_query: Dict[str, Any]) -> Task:
        """
        Task to route the parsed query to appropriate agents and coordinate execution.
        
        Args:
            parsed_query: The parsed query from parse_user_query_task
            
        Returns:
            CrewAI Task object
        """
        return Task(
            description=f"""
            Based on the parsed user query, coordinate the execution with appropriate agents:
            
            Parsed Query: {parsed_query}
            
            Your task is to:
            1. Review the parsed intent and parameters
            2. Determine the optimal sequence of agent interactions
            3. Coordinate with the required agents to fulfill the user's request
            4. Ensure all necessary information is passed between agents
            5. Handle any errors or missing information gracefully
            6. Compile the final response for the user
            
            Available agents and their capabilities:
            - RecipeManagerAgent: Database operations, recipe storage/retrieval, validation
            - RecipeScoutAgent: External recipe discovery, web scraping, API integration
            - MealPlannerAgent: Meal plan creation, nutritional analysis, calendar scheduling
            - GroceryListAgent: Grocery list generation, price optimization, inventory management
            
            Coordinate the agents in the most efficient order to complete the user's request.
            """,
            expected_output="""Complete response to the user's original query, including:
            - Direct answer to their request
            - Any recipes, meal plans, or grocery lists generated
            - Helpful additional information or suggestions
            - Clear next steps if applicable""",
            async_execution=False,
            context=[]
        )
    
    def clarify_user_intent_task(self, user_input: str, clarifying_questions: list) -> Task:
        """
        Task to ask clarifying questions when user intent is unclear.
        
        Args:
            user_input: The original user input
            clarifying_questions: List of questions to ask for clarification
            
        Returns:
            CrewAI Task object
        """
        return Task(
            description=f"""
            The user's request needs clarification. Ask intelligent follow-up questions:
            
            Original User Input: "{user_input}"
            Suggested Clarifying Questions: {clarifying_questions}
            
            Your task is to:
            1. Craft friendly, helpful clarifying questions
            2. Explain why the information is needed
            3. Provide examples or options when helpful
            4. Keep questions concise and focused
            5. Prioritize the most important missing information
            
            Make the interaction feel natural and helpful, not like an interrogation.
            """,
            expected_output="""Friendly response asking for clarification, including:
            - Brief acknowledgment of the user's request
            - Clear, specific questions to gather missing information
            - Examples or options to help the user respond
            - Explanation of how the information will help provide better results""",
            async_execution=False,
            context=[]
        ) 