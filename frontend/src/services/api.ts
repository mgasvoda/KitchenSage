/**
 * API client for KitchenSage backend.
 */

import type {
  Recipe,
  RecipeListResponse,
  MealPlan,
  MealPlanListResponse,
  GroceryList,
  GroceryListListResponse,
  ChatStreamEvent,
  ChatMessage,
  PendingRecipe,
  ParseUrlResponse,
  DiscoverRecipesResponse,
  PendingRecipeListResponse,
  ApproveRecipeResponse,
  AgentActivityEvent,
} from '../types';

const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling.
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// Recipe API
export const recipeApi = {
  list: async (params?: {
    search?: string;
    cuisine?: string;
    dietary_tags?: string[];
    difficulty?: string;
    max_prep_time?: number;
    limit?: number;
    offset?: number;
  }): Promise<RecipeListResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => searchParams.append(key, v));
          } else {
            searchParams.append(key, String(value));
          }
        }
      });
    }
    const query = searchParams.toString();
    return fetchApi<RecipeListResponse>(`/recipes${query ? `?${query}` : ''}`);
  },

  get: async (id: number): Promise<{ status: string; recipe: Recipe }> => {
    return fetchApi(`/recipes/${id}`);
  },

  create: async (recipe: Partial<Recipe>): Promise<{ status: string; recipe_id: number }> => {
    return fetchApi('/recipes', {
      method: 'POST',
      body: JSON.stringify(recipe),
    });
  },

  update: async (id: number, recipe: Partial<Recipe>): Promise<{ status: string }> => {
    return fetchApi(`/recipes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(recipe),
    });
  },

  delete: async (id: number): Promise<{ status: string }> => {
    return fetchApi(`/recipes/${id}`, {
      method: 'DELETE',
    });
  },

  discover: async (params: {
    cuisine?: string;
    dietary_restrictions?: string[];
    ingredients?: string[];
    max_prep_time?: number;
    query?: string;
  }): Promise<{ status: string; result: string }> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });
    return fetchApi(`/recipes/discover?${searchParams.toString()}`, {
      method: 'POST',
    });
  },
};

// Meal Plan API
export const mealPlanApi = {
  list: async (params?: {
    limit?: number;
    offset?: number;
  }): Promise<MealPlanListResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return fetchApi<MealPlanListResponse>(`/meal-plans${query ? `?${query}` : ''}`);
  },

  get: async (id: number): Promise<{ status: string; meal_plan: MealPlan }> => {
    return fetchApi(`/meal-plans/${id}`);
  },

  create: async (params: {
    days?: number;
    people?: number;
    prompt?: string;
    budget?: number;
  }): Promise<{ status: string; result: string }> => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });
    return fetchApi(`/meal-plans?${searchParams.toString()}`, {
      method: 'POST',
    });
  },

  /**
   * Create a meal plan with streaming agent activity updates.
   * Uses Server-Sent Events to stream real-time progress.
   */
  streamCreate: async function* (params: {
    days?: number;
    people?: number;
    prompt?: string;
    budget?: number;
  }): AsyncGenerator<AgentActivityEvent> {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else {
          searchParams.append(key, String(value));
        }
      }
    });

    const response = await fetch(`${API_BASE}/meal-plans/stream?${searchParams.toString()}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Meal plan creation failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as AgentActivityEvent;
              yield data;
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  activate: async (id: number): Promise<{ status: string; message: string; meal_plan: MealPlan }> => {
    return fetchApi(`/meal-plans/${id}/activate`, {
      method: 'POST',
    });
  },

  getActive: async (): Promise<{ status: string; message?: string; meal_plan: MealPlan | null }> => {
    return fetchApi('/meal-plans/active');
  },

  delete: async (id: number): Promise<{ status: string }> => {
    return fetchApi(`/meal-plans/${id}`, {
      method: 'DELETE',
    });
  },
};

// Grocery List API
export const groceryListApi = {
  list: async (params?: {
    limit?: number;
    offset?: number;
  }): Promise<GroceryListListResponse> => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value));
        }
      });
    }
    const query = searchParams.toString();
    return fetchApi<GroceryListListResponse>(`/grocery-lists${query ? `?${query}` : ''}`);
  },

  get: async (id: number): Promise<{ status: string; grocery_list: GroceryList }> => {
    return fetchApi(`/grocery-lists/${id}`);
  },

  /**
   * Get the default grocery list, creating one if it doesn't exist.
   */
  getDefault: async (): Promise<{ status: string; grocery_list: GroceryList }> => {
    return fetchApi('/grocery-lists/default');
  },

  generate: async (mealPlanId: number): Promise<{ status: string; result: string }> => {
    return fetchApi(`/grocery-lists?meal_plan_id=${mealPlanId}`, {
      method: 'POST',
    });
  },

  /**
   * Add ingredients from a recipe to the grocery list.
   */
  addFromRecipe: async (
    recipeId: number,
    servings?: number
  ): Promise<{ status: string; message: string; grocery_list: GroceryList }> => {
    const params = new URLSearchParams();
    params.append('recipe_id', String(recipeId));
    if (servings !== undefined) {
      params.append('servings', String(servings));
    }
    return fetchApi(`/grocery-lists/add-from-recipe?${params.toString()}`, {
      method: 'POST',
    });
  },

  /**
   * Add ingredients from a meal plan to the grocery list.
   */
  addFromMealPlan: async (
    mealPlanId: number
  ): Promise<{ status: string; message: string; grocery_list: GroceryList }> => {
    return fetchApi(`/grocery-lists/add-from-meal-plan?meal_plan_id=${mealPlanId}`, {
      method: 'POST',
    });
  },

  updateItem: async (
    listId: number,
    itemId: number,
    checked: boolean
  ): Promise<{ status: string }> => {
    return fetchApi(`/grocery-lists/${listId}/items/${itemId}?checked=${checked}`, {
      method: 'PUT',
    });
  },

  /**
   * Clear all checked/purchased items from a grocery list.
   */
  clearChecked: async (listId: number): Promise<{ status: string; deleted_count: number }> => {
    return fetchApi(`/grocery-lists/${listId}/checked`, {
      method: 'DELETE',
    });
  },

  /**
   * Clear all items from a grocery list.
   */
  clearAll: async (listId: number): Promise<{ status: string; deleted_count: number }> => {
    return fetchApi(`/grocery-lists/${listId}/items`, {
      method: 'DELETE',
    });
  },

  delete: async (id: number): Promise<{ status: string }> => {
    return fetchApi(`/grocery-lists/${id}`, {
      method: 'DELETE',
    });
  },
};

// Chat API with streaming support
export const chatApi = {
  /**
   * Send a message and stream the response using Server-Sent Events.
   */
  streamMessage: async function* (
    message: string,
    history?: ChatMessage[]
  ): AsyncGenerator<ChatStreamEvent> {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_history: history?.map(m => ({
          role: m.role,
          content: m.content,
        })),
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as ChatStreamEvent;
              yield data;
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  /**
   * Send a message synchronously (non-streaming).
   */
  sendMessage: async (
    message: string,
    history?: ChatMessage[]
  ): Promise<{ message: string; intent?: string; status: string }> => {
    return fetchApi('/chat/sync', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_history: history?.map(m => ({
          role: m.role,
          content: m.content,
        })),
      }),
    });
  },
};

// Pending Recipe API for URL parsing and AI discovery
export const pendingRecipeApi = {
  /**
   * Parse a recipe from a URL and save it for review.
   */
  parseUrl: async (url: string): Promise<ParseUrlResponse> => {
    return fetchApi('/pending-recipes/parse', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  },

  /**
   * Discover new recipes using AI-powered search.
   */
  discover: async (params: {
    query: string;
    cuisine?: string;
    dietary_restrictions?: string[];
    max_results?: number;
  }): Promise<DiscoverRecipesResponse> => {
    return fetchApi('/pending-recipes/discover', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  /**
   * List all pending recipes awaiting review.
   */
  list: async (limit?: number): Promise<PendingRecipeListResponse> => {
    const query = limit ? `?limit=${limit}` : '';
    return fetchApi(`/pending-recipes${query}`);
  },

  /**
   * Get a specific pending recipe by ID.
   */
  get: async (id: number): Promise<{ status: string; pending_recipe: PendingRecipe }> => {
    return fetchApi(`/pending-recipes/${id}`);
  },

  /**
   * Update a pending recipe before approval.
   */
  update: async (id: number, data: Partial<PendingRecipe>): Promise<{ status: string; pending_recipe: PendingRecipe }> => {
    return fetchApi(`/pending-recipes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /**
   * Approve a pending recipe and add it to the main collection.
   */
  approve: async (id: number): Promise<ApproveRecipeResponse> => {
    return fetchApi(`/pending-recipes/${id}/approve`, {
      method: 'POST',
    });
  },

  /**
   * Reject and delete a pending recipe.
   */
  reject: async (id: number): Promise<{ status: string; message: string }> => {
    return fetchApi(`/pending-recipes/${id}`, {
      method: 'DELETE',
    });
  },
};

