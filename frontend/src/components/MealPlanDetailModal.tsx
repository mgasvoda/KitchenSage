/**
 * MealPlanDetailModal - Modal for viewing detailed meal plan information
 *
 * Displays all meals organized by date and meal type, with recipe details.
 */

import { useEffect, useState } from 'react';
import { mealPlanApi } from '../services/api';
import type { MealPlan, Meal } from '../types';

interface MealPlanDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  mealPlanId: number;
}

export function MealPlanDetailModal({
  isOpen,
  onClose,
  mealPlanId,
}: MealPlanDetailModalProps) {
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && mealPlanId) {
      loadMealPlan();
    }
  }, [isOpen, mealPlanId]);

  const loadMealPlan = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await mealPlanApi.get(mealPlanId);
      if (response.status === 'success') {
        setMealPlan(response.meal_plan);
      } else {
        setError('Failed to load meal plan');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load meal plan');
    } finally {
      setLoading(false);
    }
  };

  const getMealsByDate = () => {
    if (!mealPlan) return {};

    const mealsByDate: Record<string, Record<string, Meal>> = {};

    mealPlan.meals.forEach((meal) => {
      if (!mealsByDate[meal.meal_date]) {
        mealsByDate[meal.meal_date] = {};
      }
      mealsByDate[meal.meal_date][meal.meal_type] = meal;
    });

    return mealsByDate;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric'
    });
  };

  const getMealTypeIcon = (mealType: string) => {
    switch (mealType) {
      case 'breakfast':
        return '🍳';
      case 'lunch':
        return '🥗';
      case 'dinner':
        return '🍽️';
      case 'snack':
        return '🍎';
      default:
        return '🍴';
    }
  };

  const capitalizeFirst = (str: string) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-sage-600 text-white px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-display font-bold">
              {mealPlan?.name || 'Meal Plan Details'}
            </h2>
            {mealPlan && (
              <p className="text-sage-100 text-sm mt-1">
                {formatDate(mealPlan.start_date)} - {formatDate(mealPlan.end_date)} • {mealPlan.people_count} people
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-sage-700 rounded-lg p-2 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {!loading && !error && mealPlan && (
            <div className="space-y-6">
              {/* Dietary Restrictions */}
              {mealPlan.dietary_restrictions && mealPlan.dietary_restrictions.length > 0 && (
                <div className="bg-sage-50 rounded-lg p-4">
                  <h3 className="text-sm font-semibold text-sage-700 mb-2">Dietary Restrictions</h3>
                  <div className="flex flex-wrap gap-2">
                    {mealPlan.dietary_restrictions.map((tag) => (
                      <span
                        key={tag}
                        className="px-3 py-1 bg-sage-600 text-white rounded-full text-sm"
                      >
                        {tag.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Meals by Day */}
              {Object.entries(getMealsByDate()).length === 0 ? (
                <div className="text-center py-8 text-sage-600">
                  No meals planned yet
                </div>
              ) : (
                Object.entries(getMealsByDate()).map(([date, meals]) => (
                  <div key={date} className="border border-cream-200 rounded-xl overflow-hidden">
                    <div className="bg-cream-100 px-4 py-3 border-b border-cream-200">
                      <h3 className="font-display font-bold text-sage-800">
                        {formatDate(date)}
                      </h3>
                    </div>
                    <div className="divide-y divide-cream-200">
                      {['breakfast', 'lunch', 'dinner', 'snack'].map((mealType) => {
                        const meal = meals[mealType];
                        if (!meal) return null;

                        return (
                          <div key={mealType} className="p-4 hover:bg-cream-50 transition-colors">
                            <div className="flex items-start gap-3">
                              <span className="text-2xl">{getMealTypeIcon(mealType)}</span>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-baseline gap-2 mb-1">
                                  <h4 className="text-sm font-semibold text-sage-600">
                                    {capitalizeFirst(mealType)}
                                  </h4>
                                  {meal.servings_override && (
                                    <span className="text-xs text-sage-500">
                                      {meal.servings_override} servings
                                    </span>
                                  )}
                                </div>
                                {meal.recipe ? (
                                  <div>
                                    <h5 className="font-semibold text-sage-800 mb-1">
                                      {meal.recipe.name}
                                    </h5>
                                    {meal.recipe.description && (
                                      <p className="text-sm text-sage-600 mb-2">
                                        {meal.recipe.description}
                                      </p>
                                    )}
                                    <div className="flex flex-wrap gap-3 text-xs text-sage-500">
                                      {meal.recipe.prep_time > 0 && (
                                        <span>⏱️ Prep: {meal.recipe.prep_time}min</span>
                                      )}
                                      {meal.recipe.cook_time > 0 && (
                                        <span>🔥 Cook: {meal.recipe.cook_time}min</span>
                                      )}
                                      {meal.recipe.difficulty && (
                                        <span>📊 {capitalizeFirst(meal.recipe.difficulty)}</span>
                                      )}
                                      {meal.recipe.cuisine && meal.recipe.cuisine !== 'other' && (
                                        <span>🌍 {capitalizeFirst(meal.recipe.cuisine)}</span>
                                      )}
                                    </div>
                                    {meal.recipe.dietary_tags && meal.recipe.dietary_tags.length > 0 && (
                                      <div className="mt-2 flex flex-wrap gap-1">
                                        {meal.recipe.dietary_tags.map((tag) => (
                                          <span
                                            key={tag}
                                            className="px-2 py-0.5 bg-sage-100 text-sage-700 rounded text-xs"
                                          >
                                            {tag.replace(/_/g, ' ')}
                                          </span>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <p className="text-sage-500 italic">Recipe not found</p>
                                )}
                                {meal.notes && (
                                  <p className="text-sm text-sage-600 mt-2 italic">
                                    Note: {meal.notes}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-cream-50 px-6 py-4 border-t border-cream-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-white border border-cream-300 text-sage-700 rounded-lg hover:bg-cream-100 transition-colors font-medium"
          >
            Close
          </button>
          {mealPlan && (
            <button
              className="px-4 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 transition-colors font-medium"
              onClick={() => {
                // TODO: Add grocery list generation
                console.log('Generate grocery list for plan:', mealPlan.id);
              }}
            >
              Generate Grocery List
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
