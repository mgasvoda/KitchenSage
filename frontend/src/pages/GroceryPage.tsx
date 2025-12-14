import { useState, useEffect } from 'react';
import { groceryListApi } from '../services/api';
import type { GroceryList, GroceryItem } from '../types';

export function GroceryPage() {
  const [groceryLists, setGroceryLists] = useState<GroceryList[]>([]);
  const [selectedList, setSelectedList] = useState<GroceryList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGroceryLists();
  }, []);

  const loadGroceryLists = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await groceryListApi.list({ limit: 50 });
      setGroceryLists(response.grocery_lists || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load grocery lists');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleItem = async (listId: number, itemId: number, checked: boolean) => {
    try {
      await groceryListApi.updateItem(listId, itemId, checked);
      // Update local state
      if (selectedList) {
        setSelectedList({
          ...selectedList,
          items: selectedList.items.map(item =>
            item.id === itemId ? { ...item, checked } : item
          ),
        });
      }
    } catch (err) {
      console.error('Failed to update item:', err);
    }
  };

  const groupItemsByCategory = (items: GroceryItem[]) => {
    return items.reduce((acc, item) => {
      const category = item.category || 'Other';
      if (!acc[category]) acc[category] = [];
      acc[category].push(item);
      return acc;
    }, {} as Record<string, GroceryItem[]>);
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
      case 'frozen':
        return '🧊';
      case 'pantry':
        return '🥫';
      case 'beverages':
        return '🥤';
      default:
        return '📦';
    }
  };

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-sage-800">Grocery Lists</h1>
            <p className="text-sage-600 text-sm mt-1">
              Manage your shopping lists
            </p>
          </div>
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
          </div>
        )}

        {!loading && groceryLists.length === 0 && !selectedList && (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-sage-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h2 className="text-xl font-display font-bold text-sage-800 mb-2">
              No grocery lists yet
            </h2>
            <p className="text-sage-600 mb-4">
              Create a meal plan first, then generate a grocery list from it.
            </p>
            
            {/* Demo grocery list for display */}
            <div className="max-w-md mx-auto bg-white rounded-xl shadow-sm border border-cream-200 p-6 text-left mt-8">
              <h3 className="text-lg font-display font-bold text-sage-800 mb-4">
                Sample Grocery List
              </h3>
              <div className="space-y-4">
                {[
                  { category: 'Produce', items: ['Tomatoes', 'Onions', 'Garlic'] },
                  { category: 'Protein', items: ['Chicken breast', 'Salmon'] },
                  { category: 'Dairy', items: ['Milk', 'Cheese'] },
                ].map((group) => (
                  <div key={group.category}>
                    <h4 className="text-sm font-medium text-sage-600 mb-2 flex items-center gap-2">
                      <span>{getCategoryIcon(group.category)}</span>
                      {group.category}
                    </h4>
                    <ul className="space-y-2">
                      {group.items.map((item) => (
                        <li key={item} className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            className="w-5 h-5 rounded border-cream-300 text-sage-600 focus:ring-sage-500"
                          />
                          <span className="text-sage-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Grocery Lists Grid */}
        {!selectedList && groceryLists.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {groceryLists.map((list) => (
              <div
                key={list.id}
                onClick={() => setSelectedList(list)}
                className="bg-white rounded-xl shadow-sm border border-cream-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-display font-bold text-sage-800">
                    Grocery List #{list.id}
                  </h3>
                  {list.completed && (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                      Completed
                    </span>
                  )}
                </div>
                <p className="text-sage-600 text-sm mb-2">
                  {list.items?.length || 0} items
                </p>
                {list.estimated_cost && (
                  <p className="text-terracotta-600 font-medium">
                    Est. ${list.estimated_cost.toFixed(2)}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Selected List Detail */}
        {selectedList && (
          <div className="max-w-2xl mx-auto">
            <button
              onClick={() => setSelectedList(null)}
              className="flex items-center gap-2 text-sage-600 hover:text-sage-800 mb-4"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to lists
            </button>

            <div className="bg-white rounded-xl shadow-sm border border-cream-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-display font-bold text-sage-800">
                  Grocery List #{selectedList.id}
                </h2>
                <div className="text-sm text-sage-600">
                  {selectedList.items?.filter(i => i.checked).length || 0} / {selectedList.items?.length || 0} items
                </div>
              </div>

              {selectedList.items && selectedList.items.length > 0 ? (
                <div className="space-y-6">
                  {Object.entries(groupItemsByCategory(selectedList.items)).map(([category, items]) => (
                    <div key={category}>
                      <h3 className="text-sm font-medium text-sage-600 mb-3 flex items-center gap-2 border-b border-cream-200 pb-2">
                        <span>{getCategoryIcon(category)}</span>
                        {category}
                      </h3>
                      <ul className="space-y-2">
                        {items.map((item) => (
                          <li key={item.id} className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={item.checked}
                              onChange={(e) => handleToggleItem(selectedList.id, item.id, e.target.checked)}
                              className="w-5 h-5 rounded border-cream-300 text-sage-600 focus:ring-sage-500"
                            />
                            <span className={`flex-1 ${item.checked ? 'line-through text-sage-400' : 'text-sage-700'}`}>
                              {item.ingredient_name}
                            </span>
                            <span className="text-sm text-sage-500">
                              {item.quantity} {item.unit}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sage-600 text-center py-4">No items in this list</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

