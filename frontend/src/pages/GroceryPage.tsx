import { useState, useEffect } from 'react';
import { groceryListApi } from '../services/api';
import type { GroceryList, GroceryItem } from '../types';

export function GroceryPage() {
  const [groceryList, setGroceryList] = useState<GroceryList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [showClearAllConfirm, setShowClearAllConfirm] = useState(false);

  useEffect(() => {
    loadGroceryList();
  }, []);

  const loadGroceryList = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await groceryListApi.getDefault();
      setGroceryList(response.grocery_list || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load grocery list');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleItem = async (itemId: number, checked: boolean) => {
    if (!groceryList) return;

    try {
      await groceryListApi.updateItem(groceryList.id, itemId, checked);
      // Update local state
      setGroceryList({
        ...groceryList,
        items: groceryList.items.map(item =>
          item.id === itemId
            ? { ...item, purchased: checked, status: checked ? 'purchased' : 'needed' }
            : item
        ),
      });
    } catch (err) {
      console.error('Failed to update item:', err);
    }
  };

  const handleClearChecked = async () => {
    if (!groceryList) return;
    
    try {
      setActionLoading('clearChecked');
      await groceryListApi.clearChecked(groceryList.id);
      // Reload the list to get updated items
      await loadGroceryList();
    } catch (err) {
      console.error('Failed to clear checked items:', err);
      setError(err instanceof Error ? err.message : 'Failed to clear checked items');
    } finally {
      setActionLoading(null);
    }
  };

  const handleClearAll = async () => {
    if (!groceryList) return;
    
    try {
      setActionLoading('clearAll');
      setShowClearAllConfirm(false);
      await groceryListApi.clearAll(groceryList.id);
      // Reload the list to get updated items
      await loadGroceryList();
    } catch (err) {
      console.error('Failed to clear all items:', err);
      setError(err instanceof Error ? err.message : 'Failed to clear all items');
    } finally {
      setActionLoading(null);
    }
  };

  const groupItemsByCategory = (items: GroceryItem[]) => {
    return items.reduce((acc, item) => {
      const category = item.ingredient?.category || 'other';
      // Capitalize first letter for display
      const displayCategory = category.charAt(0).toUpperCase() + category.slice(1).replace('_', ' ');
      if (!acc[displayCategory]) acc[displayCategory] = [];
      acc[displayCategory].push(item);
      return acc;
    }, {} as Record<string, GroceryItem[]>);
  };

  // Helper to check if an item is checked/purchased
  const isItemChecked = (item: GroceryItem) => {
    return item.purchased || item.status === 'purchased';
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'produce':
        return '🥬';
      case 'dairy':
        return '🥛';
      case 'meat':
      case 'protein':
        return '🥩';
      case 'bakery':
        return '🍞';
      case 'baking':
        return '🧁';
      case 'frozen':
        return '🧊';
      case 'pantry':
        return '🥫';
      case 'beverages':
        return '🥤';
      case 'seafood':
        return '🐟';
      case 'grains':
        return '🌾';
      case 'spices':
        return '🧂';
      case 'condiments':
        return '🍯';
      case 'nuts seeds':
      case 'nuts_seeds':
        return '🥜';
      case 'legumes':
        return '🫘';
      case 'canned':
        return '🥫';
      default:
        return '📦';
    }
  };

  const checkedCount = groceryList?.items?.filter(i => isItemChecked(i)).length || 0;
  const totalCount = groceryList?.items?.length || 0;
  const hasCheckedItems = checkedCount > 0;
  const hasItems = totalCount > 0;

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-sage-800">Grocery List</h1>
            <p className="text-sage-600 text-sm mt-1">
              {hasItems ? `${checkedCount} of ${totalCount} items checked` : 'Your shopping list'}
            </p>
          </div>
          
          {/* Action Buttons */}
          {hasItems && (
            <div className="flex items-center gap-3">
              {hasCheckedItems && (
                <button
                  onClick={handleClearChecked}
                  disabled={actionLoading !== null}
                  className="px-4 py-2 bg-white border border-cream-300 text-sage-700 rounded-lg hover:bg-cream-100 transition-colors font-medium text-sm disabled:opacity-50 flex items-center gap-2"
                >
                  {actionLoading === 'clearChecked' ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-sage-600 border-t-transparent"></div>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  Clear Checked
                </button>
              )}
              
              <button
                onClick={() => setShowClearAllConfirm(true)}
                disabled={actionLoading !== null}
                className="px-4 py-2 bg-white border border-red-200 text-red-600 rounded-lg hover:bg-red-50 transition-colors font-medium text-sm disabled:opacity-50 flex items-center gap-2"
              >
                {actionLoading === 'clearAll' ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-red-600 border-t-transparent"></div>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                )}
                Clear All
              </button>
            </div>
          )}
        </div>
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
            <button 
              onClick={() => setError(null)} 
              className="ml-2 text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !hasItems && (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-sage-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h2 className="text-xl font-display font-bold text-sage-800 mb-2">
              Your grocery list is empty
            </h2>
            <p className="text-sage-600 mb-4 max-w-md mx-auto">
              Add ingredients from your recipes or generate a list from a meal plan to get started.
            </p>
          </div>
        )}

        {/* Grocery List Items */}
        {!loading && groceryList && hasItems && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-xl shadow-sm border border-cream-200 p-6">
              <div className="space-y-6">
                {Object.entries(groupItemsByCategory(groceryList.items)).map(([category, items]) => (
                  <div key={category}>
                    <h3 className="text-sm font-medium text-sage-600 mb-3 flex items-center gap-2 border-b border-cream-200 pb-2">
                      <span>{getCategoryIcon(category)}</span>
                      {category}
                      <span className="text-sage-400 font-normal">({items.length})</span>
                    </h3>
                    <ul className="space-y-2">
                      {items.map((item) => {
                        const checked = isItemChecked(item);
                        return (
                          <li key={item.id} className="flex items-center gap-3 group">
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={(e) => handleToggleItem(item.id, e.target.checked)}
                              className="w-5 h-5 rounded border-cream-300 text-sage-600 focus:ring-sage-500 cursor-pointer"
                            />
                            <span className={`flex-1 transition-colors ${checked ? 'line-through text-sage-400' : 'text-sage-700'}`}>
                              {item.ingredient?.name || 'Unknown ingredient'}
                            </span>
                            <span className={`text-sm transition-colors ${checked ? 'text-sage-300' : 'text-sage-500'}`}>
                              {item.quantity} {item.unit}
                            </span>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Clear All Confirmation Modal */}
      {showClearAllConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
            <h3 className="text-lg font-display font-bold text-sage-800 mb-2">
              Clear All Items?
            </h3>
            <p className="text-sage-600 mb-6">
              This will remove all {totalCount} items from your grocery list. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowClearAllConfirm(false)}
                className="px-4 py-2 bg-white border border-cream-300 text-sage-700 rounded-lg hover:bg-cream-100 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleClearAll}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
