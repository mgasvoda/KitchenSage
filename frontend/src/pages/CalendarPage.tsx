import { useState, useEffect } from 'react';
import { mealPlanApi } from '../services/api';
import type { MealPlan } from '../types';

export function CalendarPage() {
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [createForm, setCreateForm] = useState({
    days: 7,
    people: 2,
    dietary_restrictions: [] as string[],
    budget: undefined as number | undefined,
  });

  useEffect(() => {
    loadMealPlans();
  }, []);

  const loadMealPlans = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlanApi.list({ limit: 50 });
      setMealPlans(response.meal_plans || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load meal plans');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await mealPlanApi.create(createForm);
      await loadMealPlans();
      setCreateForm({ days: 7, people: 2, dietary_restrictions: [], budget: undefined });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create meal plan');
    } finally {
      setIsCreating(false);
    }
  };

  // Generate week days for display
  const getWeekDays = () => {
    const days = [];
    const today = new Date();
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      days.push(date);
    }
    return days;
  };

  const weekDays = getWeekDays();

  const formatDay = (date: Date) => {
    return date.toLocaleDateString('en-US', { weekday: 'short' });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-sage-800">Meal Planning</h1>
            <p className="text-sage-600 text-sm mt-1">
              Plan your meals for the week
            </p>
          </div>
          <button 
            onClick={() => setIsCreating(true)}
            className="px-4 py-2 bg-terracotta-500 hover:bg-terracotta-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Plan
          </button>
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

        {/* Week View */}
        <div className="bg-white rounded-xl shadow-sm border border-cream-200 overflow-hidden mb-8">
          <div className="grid grid-cols-7 border-b border-cream-200">
            {weekDays.map((date, idx) => (
              <div
                key={idx}
                className={`p-4 text-center border-r border-cream-200 last:border-r-0 ${
                  idx === 0 ? 'bg-sage-50' : ''
                }`}
              >
                <div className="text-sm font-medium text-sage-600">{formatDay(date)}</div>
                <div className="text-lg font-bold text-sage-800">{formatDate(date)}</div>
              </div>
            ))}
          </div>

          {/* Meal slots */}
          {['Breakfast', 'Lunch', 'Dinner'].map((mealType) => (
            <div key={mealType} className="grid grid-cols-7 border-b border-cream-200 last:border-b-0">
              {weekDays.map((date, idx) => (
                <div
                  key={idx}
                  className={`p-3 min-h-[100px] border-r border-cream-200 last:border-r-0 ${
                    idx === 0 ? 'bg-sage-50' : ''
                  }`}
                >
                  {idx === 0 && (
                    <div className="text-xs font-medium text-sage-500 mb-2">{mealType}</div>
                  )}
                  <div className="text-xs text-sage-400 italic">
                    {/* Placeholder for meal */}
                    {idx === 0 && mealType === 'Breakfast' && 'Oatmeal with berries'}
                    {idx === 0 && mealType === 'Lunch' && 'Grilled chicken salad'}
                    {idx === 0 && mealType === 'Dinner' && 'Pasta primavera'}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>

        {/* Existing Meal Plans */}
        {mealPlans.length > 0 && (
          <div>
            <h2 className="text-xl font-display font-bold text-sage-800 mb-4">Your Meal Plans</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {mealPlans.map((plan) => (
                <div
                  key={plan.id}
                  className="bg-white rounded-xl shadow-sm border border-cream-200 p-6"
                >
                  <h3 className="text-lg font-display font-bold text-sage-800 mb-2">
                    {plan.name || `Meal Plan #${plan.id}`}
                  </h3>
                  <div className="text-sm text-sage-600 space-y-1">
                    <p>📅 {plan.start_date} - {plan.end_date}</p>
                    <p>👥 {plan.people_count} people</p>
                    <p>🍽️ {plan.meals?.length || 0} meals planned</p>
                  </div>
                  {plan.dietary_restrictions && plan.dietary_restrictions.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {plan.dietary_restrictions.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-sage-100 text-sage-700 rounded-full text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {!loading && mealPlans.length === 0 && (
          <div className="text-center py-8">
            <p className="text-sage-600">
              No meal plans yet. Use the "Create Plan" button or ask the chat assistant to create one!
            </p>
          </div>
        )}
      </div>

      {/* Create Plan Modal */}
      {isCreating && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
          onClick={() => setIsCreating(false)}
        >
          <div 
            className="bg-white rounded-2xl max-w-md w-full p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-display font-bold text-sage-800">
                Create Meal Plan
              </h2>
              <button
                onClick={() => setIsCreating(false)}
                className="p-2 hover:bg-cream-100 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleCreatePlan} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-sage-700 mb-1">
                  Number of Days
                </label>
                <input
                  type="number"
                  min={1}
                  max={30}
                  value={createForm.days}
                  onChange={(e) => setCreateForm({ ...createForm, days: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-sage-700 mb-1">
                  Number of People
                </label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={createForm.people}
                  onChange={(e) => setCreateForm({ ...createForm, people: parseInt(e.target.value) })}
                  className="w-full px-4 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-sage-700 mb-1">
                  Budget (optional)
                </label>
                <input
                  type="number"
                  min={0}
                  step={10}
                  value={createForm.budget || ''}
                  onChange={(e) => setCreateForm({ ...createForm, budget: e.target.value ? parseFloat(e.target.value) : undefined })}
                  placeholder="e.g., 150"
                  className="w-full px-4 py-2 border border-cream-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-400"
                />
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full px-4 py-3 bg-sage-600 hover:bg-sage-700 disabled:bg-sage-300 text-white rounded-lg font-medium transition-colors"
                >
                  {loading ? 'Creating...' : 'Create Meal Plan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

