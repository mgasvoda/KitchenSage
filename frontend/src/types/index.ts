/**
 * TypeScript type definitions for KitchenSage frontend.
 */

// Recipe types
export interface Ingredient {
  id?: number;
  name: string;
  quantity: number;
  unit: string;
  category?: string;
}

export interface RecipeIngredient {
  ingredient: Ingredient;
  quantity: number;
  unit: string;
  notes?: string;
}

export interface NutritionalInfo {
  calories?: number;
  protein?: number;
  carbohydrates?: number;
  fat?: number;
  fiber?: number;
  sodium?: number;
}

export type DifficultyLevel = 'easy' | 'medium' | 'hard';

export type CuisineType = 
  | 'american' | 'italian' | 'mexican' | 'chinese' | 'japanese'
  | 'indian' | 'french' | 'thai' | 'greek' | 'mediterranean'
  | 'spanish' | 'german' | 'korean' | 'vietnamese' | 'middle_eastern'
  | 'african' | 'fusion' | 'other';

export type DietaryTag = 
  | 'vegetarian' | 'vegan' | 'gluten_free' | 'dairy_free' | 'nut_free'
  | 'soy_free' | 'egg_free' | 'low_carb' | 'keto' | 'paleo'
  | 'whole30' | 'low_sodium' | 'low_fat' | 'high_protein'
  | 'diabetic_friendly' | 'heart_healthy';

export interface Recipe {
  id: number;
  name: string;
  description?: string;
  prep_time: number;
  cook_time: number;
  total_time?: number;
  servings: number;
  difficulty: DifficultyLevel;
  cuisine: CuisineType;
  dietary_tags: DietaryTag[];
  ingredients: RecipeIngredient[];
  instructions: string[];
  notes?: string;
  source?: string;
  image_url?: string;
  nutritional_info?: NutritionalInfo;
  created_at?: string;
  updated_at?: string;
}

// Meal Plan types
export interface Meal {
  id: number;
  meal_plan_id: number;
  recipe_id: number;
  recipe?: Recipe;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  day_number: number;
  servings_override?: number | null;
  notes?: string | null;
}

export interface MealPlan {
  id: number;
  name: string;
  is_active: boolean;
  meals: Meal[];
  people_count: number;
  dietary_restrictions: string[];
  created_at?: string;
}

// Grocery List types
export interface GroceryItem {
  id: number;
  ingredient_id: number;
  ingredient_name: string;
  quantity: number;
  unit: string;
  category: string;
  checked: boolean;
}

export interface GroceryList {
  id: number;
  meal_plan_id: number;
  items: GroceryItem[];
  estimated_cost?: number;
  created_at?: string;
  completed: boolean;
}

// Chat types
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  intent?: string;
  isStreaming?: boolean;
}

export interface ChatStreamEvent {
  type: 'start' | 'thinking' | 'token' | 'complete' | 'error' | 'done';
  content?: string;
  intent?: string;
}

// Agent Activity types for meal plan streaming
export type AgentActivityEventType = 
  | 'agent_thinking'
  | 'tool_start'
  | 'tool_result'
  | 'task_complete'
  | 'preview_update'
  | 'complete'
  | 'error'
  | 'done';

export interface AgentActivityEvent {
  type: AgentActivityEventType;
  agent?: string;
  content?: string;
  tool?: string;
  input_summary?: string;
  summary?: string;
  task?: string;
  meal_plan?: string;
  preview?: MealPlanPreview;
}

export interface MealPlanPreview {
  days: MealPlanDayPreview[];
}

export interface MealPlanDayPreview {
  date: string;
  breakfast?: string | 'pending';
  lunch?: string | 'pending';
  dinner?: string | 'pending';
}

export interface ActivityLogItem {
  id: string;
  type: AgentActivityEventType;
  content: string;
  timestamp: Date;
  isActive?: boolean;
}

// Pending Recipe types
export type PendingRecipeStatus = 'pending' | 'approved' | 'rejected';

export interface PendingRecipeIngredient {
  name: string;
  quantity?: number;
  unit?: string;
  notes?: string;
}

export interface PendingRecipe {
  id: number;
  name: string;
  description?: string;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
  difficulty?: string;
  cuisine?: string;
  dietary_tags: string[];
  ingredients: PendingRecipeIngredient[];
  instructions: string[];
  notes?: string;
  image_url?: string;
  nutritional_info?: Record<string, number>;
  source_url?: string;
  discovery_query?: string;
  status: PendingRecipeStatus;
  created_at?: string;
  is_duplicate?: boolean;
}

export interface ParseUrlResponse {
  status: string;
  message: string;
  pending_recipe?: PendingRecipe;
}

export interface DiscoverRecipesResponse {
  status: string;
  message: string;
  pending_recipes?: PendingRecipe[];
  query?: string;
}

export interface PendingRecipeListResponse {
  status: string;
  pending_recipes: PendingRecipe[];
  total: number;
}

export interface ApproveRecipeResponse {
  status: string;
  message: string;
  recipe_id?: number;
  pending_id?: number;
}

// API Response types
export interface ApiResponse<T> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
}

export interface PaginatedResponse<T> {
  status: 'success' | 'error';
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface RecipeListResponse {
  status: string;
  recipes: Recipe[];
  total: number;
  limit: number;
  offset: number;
}

export interface MealPlanListResponse {
  status: string;
  meal_plans: MealPlan[];
  total: number;
  limit: number;
  offset: number;
}

export interface GroceryListListResponse {
  status: string;
  grocery_lists: GroceryList[];
  total: number;
  limit: number;
  offset: number;
}

