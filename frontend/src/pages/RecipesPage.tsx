import { useState, useEffect, useCallback } from 'react';
import { recipeApi, groceryListApi } from '../services/api';
import type { Recipe, MealType, CuisineType, DifficultyLevel } from '../types';

// Filter options
const MEAL_TYPES: { value: MealType; label: string }[] = [
  { value: 'breakfast', label: 'Breakfast' },
  { value: 'lunch', label: 'Lunch' },
  { value: 'dinner', label: 'Dinner' },
  { value: 'snack', label: 'Snack' },
  { value: 'dessert', label: 'Dessert' },
];

const CUISINES: { value: CuisineType; label: string }[] = [
  { value: 'american', label: 'American' },
  { value: 'italian', label: 'Italian' },
  { value: 'mexican', label: 'Mexican' },
  { value: 'chinese', label: 'Chinese' },
  { value: 'japanese', label: 'Japanese' },
  { value: 'indian', label: 'Indian' },
  { value: 'french', label: 'French' },
  { value: 'thai', label: 'Thai' },
  { value: 'greek', label: 'Greek' },
  { value: 'mediterranean', label: 'Mediterranean' },
  { value: 'korean', label: 'Korean' },
  { value: 'vietnamese', label: 'Vietnamese' },
  { value: 'middle_eastern', label: 'Middle Eastern' },
  { value: 'other', label: 'Other' },
];

const DIFFICULTIES: { value: DifficultyLevel; label: string }[] = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
];

export function RecipesPage() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMealTypes, setSelectedMealTypes] = useState<MealType[]>([]);
  const [selectedCuisine, setSelectedCuisine] = useState<CuisineType | ''>('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<DifficultyLevel | ''>('');
  const [maxPrepTime, setMaxPrepTime] = useState<number | ''>('');
  const [maxTotalTime, setMaxTotalTime] = useState<number | ''>('');
  const [showFilters, setShowFilters] = useState(false);
  
  // UI state
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [addingToGrocery, setAddingToGrocery] = useState(false);
  const [groceryMessage, setGroceryMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadRecipes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Build search params
      const params: Record<string, unknown> = { limit: 50 };
      
      if (searchQuery) params.query = searchQuery;
      if (selectedMealTypes.length > 0) params.meal_types = selectedMealTypes;
      if (selectedCuisine) params.cuisine = selectedCuisine;
      if (selectedDifficulty) params.difficulty = selectedDifficulty;
      if (maxPrepTime) params.max_prep_time = maxPrepTime;
      if (maxTotalTime) params.max_total_time = maxTotalTime;
      
      // Use the advanced search endpoint
      const response = await recipeApi.search(params);
      
      // Extract recipes from the response
      const recipeList = response.recipes?.map(r => r.recipe) || [];
      setRecipes(recipeList);
      setTotalResults(response.total || recipeList.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recipes');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedMealTypes, selectedCuisine, selectedDifficulty, maxPrepTime, maxTotalTime]);

  useEffect(() => {
    loadRecipes();
  }, [loadRecipes]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadRecipes();
  };

  const clearFilters = () => {
    setSelectedMealTypes([]);
    setSelectedCuisine('');
    setSelectedDifficulty('');
    setMaxPrepTime('');
    setMaxTotalTime('');
  };

  const hasActiveFilters = selectedMealTypes.length > 0 || selectedCuisine || selectedDifficulty || maxPrepTime || maxTotalTime;

  const toggleMealType = (type: MealType) => {
    setSelectedMealTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-700';
      case 'medium': return 'bg-yellow-100 text-yellow-700';
      case 'hard': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const handleAddToGroceryList = async (recipe: Recipe) => {
    try {
      setAddingToGrocery(true);
      setGroceryMessage(null);
      const response = await groceryListApi.addFromRecipe(recipe.id, recipe.servings);
      setGroceryMessage({ type: 'success', text: response.message || 'Added to grocery list!' });
      // Clear message after 3 seconds
      setTimeout(() => setGroceryMessage(null), 3000);
    } catch (err) {
      setGroceryMessage({ 
        type: 'error', 
        text: err instanceof Error ? err.message : 'Failed to add to grocery list' 
      });
    } finally {
      setAddingToGrocery(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-sage-800">Recipes</h1>
            <p className="text-sage-600 text-sm mt-1">
              {loading ? 'Loading...' : `${totalResults} recipe${totalResults !== 1 ? 's' : ''} found`}
            </p>
          </div>
          <button className="px-4 py-2 bg-terracotta-500 hover:bg-terracotta-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Recipe
          </button>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mt-4 flex gap-3">
          <div className="flex-1 max-w-xl relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search recipes... (try 'quick weeknight dinners' or 'healthy vegetarian')"
              className="w-full px-4 py-2 pl-10 bg-cream-50 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400 text-sage-800"
            />
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors"
          >
            Search
          </button>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 border rounded-lg font-medium transition-colors flex items-center gap-2 ${
              showFilters || hasActiveFilters
                ? 'bg-sage-100 border-sage-400 text-sage-700'
                : 'bg-white border-cream-300 text-sage-600 hover:bg-cream-50'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
            Filters
            {hasActiveFilters && (
              <span className="ml-1 px-1.5 py-0.5 bg-terracotta-500 text-white text-xs rounded-full">
                {[selectedMealTypes.length > 0, selectedCuisine, selectedDifficulty, maxPrepTime, maxTotalTime].filter(Boolean).length}
              </span>
            )}
          </button>
        </form>

        {/* Expandable Filters */}
        {showFilters && (
          <div className="mt-4 p-4 bg-cream-50 rounded-lg border border-cream-200 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Meal Type */}
              <div>
                <label className="block text-sm font-medium text-sage-700 mb-2">Meal Type</label>
                <div className="flex flex-wrap gap-2">
                  {MEAL_TYPES.map(({ value, label }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => toggleMealType(value)}
                      className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                        selectedMealTypes.includes(value)
                          ? 'bg-sage-600 text-white'
                          : 'bg-white border border-cream-300 text-sage-600 hover:bg-cream-100'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Cuisine */}
              <div>
                <label className="block text-sm font-medium text-sage-700 mb-2">Cuisine</label>
                <select
                  value={selectedCuisine}
                  onChange={(e) => setSelectedCuisine(e.target.value as CuisineType | '')}
                  className="w-full px-3 py-2 bg-white border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400 text-sage-800"
                >
                  <option value="">Any Cuisine</option>
                  {CUISINES.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              {/* Difficulty */}
              <div>
                <label className="block text-sm font-medium text-sage-700 mb-2">Difficulty</label>
                <select
                  value={selectedDifficulty}
                  onChange={(e) => setSelectedDifficulty(e.target.value as DifficultyLevel | '')}
                  className="w-full px-3 py-2 bg-white border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400 text-sage-800"
                >
                  <option value="">Any Difficulty</option>
                  {DIFFICULTIES.map(({ value, label }) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>

              {/* Time Filters */}
              <div>
                <label className="block text-sm font-medium text-sage-700 mb-2">Max Time</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number"
                    value={maxPrepTime}
                    onChange={(e) => setMaxPrepTime(e.target.value ? parseInt(e.target.value) : '')}
                    placeholder="Prep (min)"
                    min="0"
                    className="w-full px-3 py-2 bg-white border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400 text-sage-800 text-sm"
                  />
                  <input
                    type="number"
                    value={maxTotalTime}
                    onChange={(e) => setMaxTotalTime(e.target.value ? parseInt(e.target.value) : '')}
                    placeholder="Total (min)"
                    min="0"
                    className="w-full px-3 py-2 bg-white border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400 text-sage-800 text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Filter Actions */}
            {hasActiveFilters && (
              <div className="mt-4 flex justify-end">
                <button
                  type="button"
                  onClick={clearFilters}
                  className="text-sm text-sage-600 hover:text-sage-800 underline"
                >
                  Clear all filters
                </button>
              </div>
            )}
          </div>
        )}
      </header>

      {/* Content */}
      <div className="p-6">
        {loading && (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-sage-600 border-t-transparent"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-4">
            {error}
          </div>
        )}

        {!loading && recipes.length === 0 && (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-sage-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h2 className="text-xl font-display font-bold text-sage-800 mb-2">
              No recipes yet
            </h2>
            <p className="text-sage-600">
              Start by adding your first recipe or discovering new ones!
            </p>
          </div>
        )}

        {/* Recipe Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recipes.map((recipe) => (
            <div
              key={recipe.id}
              onClick={() => setSelectedRecipe(recipe)}
              className="bg-white rounded-xl shadow-sm border border-cream-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer animate-fade-in"
            >
              {recipe.image_url ? (
                <img
                  src={recipe.image_url}
                  alt={recipe.name}
                  className="w-full h-48 object-cover"
                />
              ) : (
                <div className="w-full h-48 bg-gradient-to-br from-sage-200 to-sage-300 flex items-center justify-center">
                  <svg className="w-16 h-16 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} 
                      d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
              )}
              <div className="p-4">
                <h3 className="text-lg font-display font-bold text-sage-800 mb-2">
                  {recipe.name}
                </h3>
                <p className="text-sage-600 text-sm line-clamp-2 mb-3">
                  {recipe.description || 'No description available'}
                </p>
                <div className="flex items-center gap-3 text-sm">
                  <span className="flex items-center gap-1 text-sage-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {recipe.prep_time + recipe.cook_time} min
                  </span>
                  <span className="flex items-center gap-1 text-sage-500">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    {recipe.servings}
                  </span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(recipe.difficulty)}`}>
                    {recipe.difficulty}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recipe Detail Modal */}
      {selectedRecipe && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedRecipe(null)}
        >
          <div 
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-2xl font-display font-bold text-sage-800">
                  {selectedRecipe.name}
                </h2>
                <button
                  onClick={() => setSelectedRecipe(null)}
                  className="p-2 hover:bg-cream-100 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {selectedRecipe.description && (
                <p className="text-sage-600 mb-4">{selectedRecipe.description}</p>
              )}

              <div className="flex flex-wrap gap-2 mb-6">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(selectedRecipe.difficulty)}`}>
                  {selectedRecipe.difficulty}
                </span>
                <span className="px-3 py-1 bg-sage-100 text-sage-700 rounded-full text-sm">
                  {selectedRecipe.cuisine}
                </span>
                {selectedRecipe.meal_types?.map((type) => (
                  <span key={type} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                    {type}
                  </span>
                ))}
                {selectedRecipe.dietary_tags?.map((tag) => (
                  <span key={tag} className="px-3 py-1 bg-terracotta-100 text-terracotta-700 rounded-full text-sm">
                    {tag.replace('_', ' ')}
                  </span>
                ))}
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-cream-50 rounded-lg">
                <div className="text-center">
                  <div className="text-2xl font-bold text-sage-800">{selectedRecipe.prep_time}</div>
                  <div className="text-sm text-sage-600">Prep (min)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-sage-800">{selectedRecipe.cook_time}</div>
                  <div className="text-sm text-sage-600">Cook (min)</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-sage-800">{selectedRecipe.servings}</div>
                  <div className="text-sm text-sage-600">Servings</div>
                </div>
              </div>

              {selectedRecipe.ingredients && selectedRecipe.ingredients.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-display font-bold text-sage-800 mb-3">Ingredients</h3>
                  <ul className="space-y-2">
                    {selectedRecipe.ingredients.map((ing, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sage-700">
                        <span className="w-2 h-2 bg-terracotta-400 rounded-full"></span>
                        {ing.quantity} {ing.unit} {ing.ingredient?.name || ing}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedRecipe.instructions && selectedRecipe.instructions.length > 0 && (
                <div>
                  <h3 className="text-lg font-display font-bold text-sage-800 mb-3">Instructions</h3>
                  <ol className="space-y-3">
                    {selectedRecipe.instructions.map((step, idx) => (
                      <li key={idx} className="flex gap-3 text-sage-700">
                        <span className="flex-shrink-0 w-6 h-6 bg-sage-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                          {idx + 1}
                        </span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}

              {/* Grocery List Feedback */}
              {groceryMessage && (
                <div className={`mt-4 p-3 rounded-lg ${
                  groceryMessage.type === 'success' 
                    ? 'bg-green-50 text-green-700 border border-green-200' 
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  {groceryMessage.text}
                </div>
              )}

              {/* Footer with Action Button */}
              <div className="mt-6 pt-4 border-t border-cream-200 flex justify-end">
                <button
                  onClick={() => handleAddToGroceryList(selectedRecipe)}
                  disabled={addingToGrocery}
                  className="px-4 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 transition-colors font-medium disabled:opacity-50 flex items-center gap-2"
                >
                  {addingToGrocery ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  )}
                  Add to Grocery List
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

