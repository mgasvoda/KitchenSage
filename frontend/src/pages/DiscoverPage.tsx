import { useState, useEffect } from 'react';
import { pendingRecipeApi } from '../services/api';
import type { PendingRecipe, PendingRecipeIngredient } from '../types';

type TabType = 'url' | 'search' | 'pending';

export function DiscoverPage() {
  const [activeTab, setActiveTab] = useState<TabType>('url');
  
  // URL Parser state
  const [url, setUrl] = useState('');
  const [parsingUrl, setParsingUrl] = useState(false);
  const [parsedRecipe, setParsedRecipe] = useState<PendingRecipe | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  
  // AI Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCuisine, setSearchCuisine] = useState('');
  const [searchDietary, setSearchDietary] = useState<string[]>([]);
  const [searching, setSearching] = useState(false);
  const [discoveredRecipes, setDiscoveredRecipes] = useState<PendingRecipe[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  
  // Pending queue state
  const [pendingRecipes, setPendingRecipes] = useState<PendingRecipe[]>([]);
  const [loadingPending, setLoadingPending] = useState(false);
  const [pendingError, setPendingError] = useState<string | null>(null);
  
  // Edit modal state
  const [editingRecipe, setEditingRecipe] = useState<PendingRecipe | null>(null);
  const [editForm, setEditForm] = useState<Partial<PendingRecipe>>({});
  
  // Action state
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    loadPendingRecipes();
  }, []);

  const loadPendingRecipes = async () => {
    setLoadingPending(true);
    setPendingError(null);
    try {
      const response = await pendingRecipeApi.list(50);
      setPendingRecipes(response.pending_recipes || []);
    } catch (err) {
      setPendingError(err instanceof Error ? err.message : 'Failed to load pending recipes');
    } finally {
      setLoadingPending(false);
    }
  };

  const handleParseUrl = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim() || parsingUrl) return;
    
    setParsingUrl(true);
    setParseError(null);
    setParsedRecipe(null);
    
    try {
      const response = await pendingRecipeApi.parseUrl(url.trim());
      if (response.pending_recipe) {
        setParsedRecipe(response.pending_recipe);
        loadPendingRecipes(); // Refresh pending list
      } else if (response.status === 'duplicate') {
        setParseError(response.message);
      }
    } catch (err) {
      setParseError(err instanceof Error ? err.message : 'Failed to parse URL');
    } finally {
      setParsingUrl(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || searching) return;
    
    setSearching(true);
    setSearchError(null);
    setDiscoveredRecipes([]);
    
    try {
      const response = await pendingRecipeApi.discover({
        query: searchQuery.trim(),
        cuisine: searchCuisine || undefined,
        dietary_restrictions: searchDietary.length > 0 ? searchDietary : undefined,
        max_results: 5,
      });
      setDiscoveredRecipes(response.pending_recipes || []);
      loadPendingRecipes(); // Refresh pending list
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleApprove = async (id: number) => {
    setActionLoading(id);
    try {
      await pendingRecipeApi.approve(id);
      loadPendingRecipes();
      setParsedRecipe(null);
      setDiscoveredRecipes(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      console.error('Failed to approve recipe:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: number) => {
    setActionLoading(id);
    try {
      await pendingRecipeApi.reject(id);
      loadPendingRecipes();
      setParsedRecipe(null);
      setDiscoveredRecipes(prev => prev.filter(r => r.id !== id));
    } catch (err) {
      console.error('Failed to reject recipe:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleEdit = (recipe: PendingRecipe) => {
    setEditingRecipe(recipe);
    setEditForm({
      name: recipe.name,
      description: recipe.description,
      prep_time: recipe.prep_time,
      cook_time: recipe.cook_time,
      servings: recipe.servings,
      difficulty: recipe.difficulty,
      cuisine: recipe.cuisine,
      instructions: recipe.instructions,
    });
  };

  const handleSaveEdit = async () => {
    if (!editingRecipe) return;
    
    setActionLoading(editingRecipe.id);
    try {
      await pendingRecipeApi.update(editingRecipe.id, editForm);
      loadPendingRecipes();
      setEditingRecipe(null);
    } catch (err) {
      console.error('Failed to update recipe:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const toggleDietary = (tag: string) => {
    setSearchDietary(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const cuisineOptions = [
    'italian', 'mexican', 'chinese', 'japanese', 'indian',
    'french', 'thai', 'greek', 'mediterranean', 'american'
  ];

  const dietaryOptions = [
    'vegetarian', 'vegan', 'gluten_free', 'dairy_free', 'keto', 'paleo'
  ];

  const renderRecipeCard = (recipe: PendingRecipe, showActions = true) => (
    <div 
      key={recipe.id}
      className="bg-white rounded-xl shadow-sm border border-cream-200 p-4 animate-fade-in"
    >
      <div className="flex justify-between items-start mb-3">
        <h3 className="text-lg font-display font-bold text-sage-800">{recipe.name}</h3>
        {recipe.is_duplicate && (
          <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full">
            Duplicate
          </span>
        )}
      </div>
      
      {recipe.description && (
        <p className="text-sage-600 text-sm mb-3 line-clamp-2">{recipe.description}</p>
      )}
      
      <div className="flex flex-wrap gap-2 mb-3 text-sm">
        {recipe.prep_time && (
          <span className="flex items-center gap-1 text-sage-500">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {(recipe.prep_time || 0) + (recipe.cook_time || 0)} min
          </span>
        )}
        {recipe.servings && (
          <span className="text-sage-500">{recipe.servings} servings</span>
        )}
        {recipe.difficulty && (
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            recipe.difficulty.toLowerCase() === 'easy' ? 'bg-green-100 text-green-700' :
            recipe.difficulty.toLowerCase() === 'hard' ? 'bg-red-100 text-red-700' :
            'bg-yellow-100 text-yellow-700'
          }`}>
            {recipe.difficulty}
          </span>
        )}
        {recipe.cuisine && (
          <span className="px-2 py-0.5 bg-sage-100 text-sage-700 rounded-full text-xs">
            {recipe.cuisine}
          </span>
        )}
      </div>
      
      {recipe.ingredients.length > 0 && (
        <div className="mb-3">
          <p className="text-xs text-sage-500 mb-1">Ingredients ({recipe.ingredients.length})</p>
          <div className="flex flex-wrap gap-1">
            {recipe.ingredients.slice(0, 5).map((ing: PendingRecipeIngredient, idx: number) => (
              <span key={idx} className="text-xs bg-cream-100 text-sage-700 px-2 py-0.5 rounded">
                {ing.name}
              </span>
            ))}
            {recipe.ingredients.length > 5 && (
              <span className="text-xs text-sage-500">+{recipe.ingredients.length - 5} more</span>
            )}
          </div>
        </div>
      )}
      
      {recipe.source_url && (
        <a 
          href={recipe.source_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-xs text-terracotta-600 hover:underline mb-3 block truncate"
        >
          {recipe.source_url}
        </a>
      )}
      
      {showActions && (
        <div className="flex gap-2 mt-4 pt-3 border-t border-cream-200">
          <button
            onClick={() => handleApprove(recipe.id)}
            disabled={actionLoading === recipe.id}
            className="flex-1 px-3 py-2 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {actionLoading === recipe.id ? 'Saving...' : 'Approve'}
          </button>
          <button
            onClick={() => handleEdit(recipe)}
            disabled={actionLoading === recipe.id}
            className="px-3 py-2 bg-sage-100 hover:bg-sage-200 text-sage-700 rounded-lg text-sm font-medium transition-colors"
          >
            Edit
          </button>
          <button
            onClick={() => handleReject(recipe.id)}
            disabled={actionLoading === recipe.id}
            className="px-3 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm font-medium transition-colors"
          >
            Reject
          </button>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <h1 className="text-2xl font-display font-bold text-sage-800">Discover Recipes</h1>
        <p className="text-sage-600 text-sm mt-1">
          Add new recipes by URL or discover them with AI search
        </p>
      </header>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-cream-200">
        <div className="px-6 flex gap-1">
          {[
            { id: 'url' as TabType, label: 'Add by URL', icon: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1' },
            { id: 'search' as TabType, label: 'AI Search', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
            { id: 'pending' as TabType, label: `Pending Review${pendingRecipes.length > 0 ? ` (${pendingRecipes.length})` : ''}`, icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-terracotta-500 text-terracotta-600'
                  : 'border-transparent text-sage-600 hover:text-sage-800'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
              </svg>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* URL Parser Tab */}
        {activeTab === 'url' && (
          <div className="max-w-2xl mx-auto">
            <form onSubmit={handleParseUrl} className="mb-6">
              <label className="block text-sm font-medium text-sage-700 mb-2">
                Recipe URL
              </label>
              <div className="flex gap-3">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/recipe/..."
                  className="flex-1 px-4 py-3 bg-white border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400 text-sage-800"
                  disabled={parsingUrl}
                />
                <button
                  type="submit"
                  disabled={parsingUrl || !url.trim()}
                  className="px-6 py-3 bg-terracotta-500 hover:bg-terracotta-600 disabled:bg-terracotta-300 text-white rounded-lg font-medium transition-colors"
                >
                  {parsingUrl ? 'Parsing...' : 'Parse Recipe'}
                </button>
              </div>
              <p className="text-xs text-sage-500 mt-2">
                Paste a URL from a recipe website and we'll extract the recipe details for you.
              </p>
            </form>

            {parseError && (
              <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
                {parseError}
              </div>
            )}

            {parsedRecipe && renderRecipeCard(parsedRecipe)}
          </div>
        )}

        {/* AI Search Tab */}
        {activeTab === 'search' && (
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSearch} className="mb-6 bg-white p-6 rounded-xl shadow-sm border border-cream-200">
              <div className="mb-4">
                <label className="block text-sm font-medium text-sage-700 mb-2">
                  What are you looking for?
                </label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g., quick weeknight pasta, healthy chicken dinner, vegetarian curry..."
                  className="w-full px-4 py-3 bg-cream-50 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400 text-sage-800"
                  disabled={searching}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-sage-700 mb-2">
                    Cuisine (optional)
                  </label>
                  <select
                    value={searchCuisine}
                    onChange={(e) => setSearchCuisine(e.target.value)}
                    className="w-full px-4 py-2 bg-cream-50 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400 text-sage-800"
                    disabled={searching}
                  >
                    <option value="">Any cuisine</option>
                    {cuisineOptions.map((cuisine) => (
                      <option key={cuisine} value={cuisine}>
                        {cuisine.charAt(0).toUpperCase() + cuisine.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-sage-700 mb-2">
                    Dietary Preferences (optional)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {dietaryOptions.map((tag) => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => toggleDietary(tag)}
                        disabled={searching}
                        className={`px-3 py-1 rounded-full text-sm transition-colors ${
                          searchDietary.includes(tag)
                            ? 'bg-terracotta-500 text-white'
                            : 'bg-cream-100 text-sage-700 hover:bg-cream-200'
                        }`}
                      >
                        {tag.replace(/_/g, ' ')}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={searching || !searchQuery.trim()}
                className="w-full px-6 py-3 bg-terracotta-500 hover:bg-terracotta-600 disabled:bg-terracotta-300 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                {searching ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Searching...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Discover Recipes
                  </>
                )}
              </button>
            </form>

            {searchError && (
              <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
                {searchError}
              </div>
            )}

            {discoveredRecipes.length > 0 && (
              <div>
                <h2 className="text-lg font-display font-bold text-sage-800 mb-4">
                  Discovered Recipes ({discoveredRecipes.length})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {discoveredRecipes.map((recipe) => renderRecipeCard(recipe))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Pending Queue Tab */}
        {activeTab === 'pending' && (
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-display font-bold text-sage-800">
                Recipes Awaiting Review
              </h2>
              <button
                onClick={loadPendingRecipes}
                disabled={loadingPending}
                className="px-4 py-2 bg-sage-100 hover:bg-sage-200 text-sage-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
              >
                <svg className={`w-4 h-4 ${loadingPending ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </button>
            </div>

            {pendingError && (
              <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
                {pendingError}
              </div>
            )}

            {loadingPending && (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-sage-600 border-t-transparent"></div>
              </div>
            )}

            {!loadingPending && pendingRecipes.length === 0 && (
              <div className="text-center py-12 bg-white rounded-xl border border-cream-200">
                <div className="w-16 h-16 bg-sage-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-display font-bold text-sage-800 mb-2">
                  All caught up!
                </h3>
                <p className="text-sage-600">
                  No recipes pending review. Add some using URL or AI Search.
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pendingRecipes.map((recipe) => renderRecipeCard(recipe))}
            </div>
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingRecipe && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setEditingRecipe(null)}
        >
          <div 
            className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-xl font-display font-bold text-sage-800">
                  Edit Recipe
                </h2>
                <button
                  onClick={() => setEditingRecipe(null)}
                  className="p-2 hover:bg-cream-100 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-sage-700 mb-1">Name</label>
                  <input
                    type="text"
                    value={editForm.name || ''}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-sage-700 mb-1">Description</label>
                  <textarea
                    value={editForm.description || ''}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    rows={2}
                    className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400"
                  />
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-sage-700 mb-1">Prep Time (min)</label>
                    <input
                      type="number"
                      value={editForm.prep_time || ''}
                      onChange={(e) => setEditForm({ ...editForm, prep_time: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-sage-700 mb-1">Cook Time (min)</label>
                    <input
                      type="number"
                      value={editForm.cook_time || ''}
                      onChange={(e) => setEditForm({ ...editForm, cook_time: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-sage-700 mb-1">Servings</label>
                    <input
                      type="number"
                      value={editForm.servings || ''}
                      onChange={(e) => setEditForm({ ...editForm, servings: parseInt(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-sage-700 mb-1">Difficulty</label>
                    <select
                      value={editForm.difficulty || ''}
                      onChange={(e) => setEditForm({ ...editForm, difficulty: e.target.value })}
                      className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400"
                    >
                      <option value="">Select...</option>
                      <option value="Easy">Easy</option>
                      <option value="Medium">Medium</option>
                      <option value="Hard">Hard</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-sage-700 mb-1">Cuisine</label>
                    <input
                      type="text"
                      value={editForm.cuisine || ''}
                      onChange={(e) => setEditForm({ ...editForm, cuisine: e.target.value })}
                      className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-sage-700 mb-1">
                    Instructions (one per line)
                  </label>
                  <textarea
                    value={(editForm.instructions || []).join('\n')}
                    onChange={(e) => setEditForm({ 
                      ...editForm, 
                      instructions: e.target.value.split('\n').filter(s => s.trim()) 
                    })}
                    rows={6}
                    className="w-full px-3 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terracotta-400 font-mono text-sm"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={handleSaveEdit}
                  disabled={actionLoading === editingRecipe.id}
                  className="flex-1 px-4 py-2 bg-terracotta-500 hover:bg-terracotta-600 disabled:bg-terracotta-300 text-white rounded-lg font-medium transition-colors"
                >
                  {actionLoading === editingRecipe.id ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={() => setEditingRecipe(null)}
                  className="px-4 py-2 bg-cream-100 hover:bg-cream-200 text-sage-700 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

