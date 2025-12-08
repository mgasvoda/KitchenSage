import { useState, useEffect } from 'react';
import { recipeApi } from '../services/api';
import type { Recipe } from '../types';

export function RecipesPage() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);

  useEffect(() => {
    loadRecipes();
  }, []);

  const loadRecipes = async (searchTerm?: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await recipeApi.list({ search: searchTerm, limit: 50 });
      setRecipes(response.recipes || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recipes');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadRecipes(search);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-700';
      case 'medium': return 'bg-yellow-100 text-yellow-700';
      case 'hard': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
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
              Browse and manage your recipe collection
            </p>
          </div>
          <button className="px-4 py-2 bg-terracotta-500 hover:bg-terracotta-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Recipe
          </button>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="mt-4 flex gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search recipes..."
            className="flex-1 max-w-md px-4 py-2 bg-cream-50 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400 text-sage-800"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors"
          >
            Search
          </button>
        </form>
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

