import { useState, useEffect, useRef } from 'react';
import { mealPlanApi, groceryListApi } from '../services/api';
import { AgentActivityPanel } from '../components/AgentActivityPanel';
import { MealPlanDetailModal } from '../components/MealPlanDetailModal';
import type { MealPlan, AgentActivityEvent } from '../types';
import { useNavigate } from 'react-router-dom';
import { getDefaultPeopleCount } from '../services/settings';

export function MealPlansPage() {
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreatePanel, setShowCreatePanel] = useState(false);
  const [eventStream, setEventStream] = useState<AsyncGenerator<AgentActivityEvent> | null>(null);
  const [createForm, setCreateForm] = useState({
    prompt: '',
    budget: undefined as number | undefined,
  });
  const [selectedMealPlanId, setSelectedMealPlanId] = useState<number | null>(null);
  const streamRef = useRef<AsyncGenerator<AgentActivityEvent> | null>(null);
  const navigate = useNavigate();

  const [toast, setToast] = useState<{
    type: 'info' | 'success' | 'error';
    message: string;
    actionLabel?: string;
    onAction?: () => void;
    dismissAfterMs?: number;
  } | null>(null);

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

  const handleStartCreate = () => {
    // Start the streaming meal plan creation
    const stream = mealPlanApi.streamCreate({
      prompt: createForm.prompt,
      budget: createForm.budget,
      people: getDefaultPeopleCount(),
      // days intentionally omitted; inferred from prompt server-side
    });
    streamRef.current = stream;
    setEventStream(stream);
    setShowCreatePanel(true);
  };

  const handlePanelComplete = async (_mealPlan: string) => {
    // Reload meal plans after completion
    await loadMealPlans();
    setCreateForm({ prompt: '', budget: undefined });
  };

  const handlePanelClose = () => {
    setShowCreatePanel(false);
    setEventStream(null);
    streamRef.current = null;
  };

  const handleActivate = async (planId: number, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent opening the detail modal
    try {
      await mealPlanApi.activate(planId);
      await loadMealPlans(); // Reload to show updated active status
    } catch (err) {
      console.error('Failed to activate meal plan:', err);
    }
  };

  const getDayCount = (plan: MealPlan) => {
    if (!plan.meals || plan.meals.length === 0) return 0;
    const dayNumbers = plan.meals.map(m => m.day_number);
    return Math.max(...dayNumbers);
  };

  const showToast = (next: {
    type: 'info' | 'success' | 'error';
    message: string;
    actionLabel?: string;
    onAction?: () => void;
    dismissAfterMs?: number;
  }) => {
    setToast(next);
    if (next.dismissAfterMs && next.dismissAfterMs > 0) {
      window.setTimeout(() => setToast((current) => (current === next ? null : current)), next.dismissAfterMs);
    }
  };

  const handleAddMealPlanToGroceryList = async (mealPlanId: number) => {
    const plan = mealPlans.find(p => p.id === mealPlanId);

    showToast({
      type: 'info',
      message: `Adding ${plan?.name || 'meal plan'} to your grocery list…`,
    });

    try {
      const response = await groceryListApi.addFromMealPlan(mealPlanId);
      showToast({
        type: 'success',
        message: response.message || 'Added to grocery list!',
        actionLabel: 'View grocery list',
        onAction: () => navigate('/grocery'),
        dismissAfterMs: 5000,
      });
    } catch (err) {
      showToast({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to add to grocery list',
        dismissAfterMs: 7000,
      });
    }
  };

  return (
    <div className="min-h-screen bg-cream-50">
      {/* Header */}
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-sage-800">Meal Plans</h1>
            <p className="text-sage-600 text-sm mt-1">
              Manage and organize your meal plans
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

        {/* Create New Plan Card */}
        <div className="bg-gradient-to-br from-sage-600 to-sage-700 rounded-2xl shadow-xl p-6 mb-8 text-white">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="text-xl font-display font-bold mb-2">Create AI Meal Plan</h2>
              <p className="text-sage-100 text-sm">
                Let our AI chef plan your meals with real-time progress updates
              </p>
            </div>
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="md:col-span-1">
              <div className="text-sm font-medium text-sage-100 mb-1">
                Planning for
              </div>
              <div className="px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white">
                {getDefaultPeopleCount()} people
              </div>
              <p className="text-xs text-sage-200 mt-2">
                Change this in Settings.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-sage-100 mb-1">
                Budget (optional)
              </label>
              <input
                type="number"
                min={0}
                step={10}
                value={createForm.budget || ''}
                onChange={(e) => setCreateForm({ ...createForm, budget: e.target.value ? parseFloat(e.target.value) : undefined })}
                placeholder="e.g., 150"
                className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
            </div>
          </div>

          {/* Preferences Prompt */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-sage-100 mb-2">
              Preferences & Instructions
            </label>
            <textarea
              value={createForm.prompt}
              onChange={(e) => setCreateForm({ ...createForm, prompt: e.target.value })}
              placeholder="Tell us about your preferences... e.g., 'vegetarian meals with Italian cuisine focus', 'quick weeknight dinners under 30 minutes', 'high protein, low carb for weight loss', 'kid-friendly meals my picky eater will love'"
              rows={3}
              className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-white/30 resize-none"
            />
          </div>

          <button
            onClick={handleStartCreate}
            className="w-full py-3 bg-white text-sage-700 hover:bg-sage-50 rounded-xl font-bold transition-colors shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Generate AI Meal Plan
          </button>
        </div>

        {/* Existing Meal Plans */}
        {mealPlans.length > 0 && (
          <div>
            <h2 className="text-xl font-display font-bold text-sage-800 mb-4">Your Meal Plans</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {mealPlans.map((plan) => (
                <div
                  key={plan.id}
                  className={`bg-white rounded-xl shadow-sm border p-6 hover:shadow-lg transition-all cursor-pointer ${
                    plan.is_active ? 'border-terracotta-400 ring-2 ring-terracotta-200' : 'border-cream-200 hover:border-sage-300'
                  }`}
                  onClick={() => setSelectedMealPlanId(plan.id)}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-display font-bold text-sage-800 flex-1">
                      {plan.name || `Meal Plan #${plan.id}`}
                    </h3>
                    {plan.is_active && (
                      <span className="px-2 py-0.5 bg-terracotta-500 text-white rounded text-xs font-medium">
                        Active
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-sage-600 space-y-1">
                    <p>📅 {getDayCount(plan)}-day plan</p>
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
                          {tag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="mt-4 pt-4 border-t border-cream-200 flex items-center justify-between">
                    <button className="text-sage-600 hover:text-sage-700 text-sm font-medium flex items-center gap-1">
                      View Details
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                    {!plan.is_active && (
                      <button
                        onClick={(e) => handleActivate(plan.id, e)}
                        className="px-3 py-1 bg-terracotta-500 hover:bg-terracotta-600 text-white rounded text-xs font-medium transition-colors"
                      >
                        Set Active
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!loading && mealPlans.length === 0 && (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-sage-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <p className="text-sage-600 mb-2">
              No meal plans yet
            </p>
            <p className="text-sage-500 text-sm">
              Use the form above to create your first AI-powered meal plan!
            </p>
          </div>
        )}
      </div>

      {/* Agent Activity Panel */}
      <AgentActivityPanel
        isOpen={showCreatePanel}
        onClose={handlePanelClose}
        onComplete={handlePanelComplete}
        eventStream={eventStream}
        planConfig={{
          people: getDefaultPeopleCount(),
          prompt: createForm.prompt,
          budget: createForm.budget,
        }}
      />

      {/* Meal Plan Detail Modal */}
      {selectedMealPlanId && (
        <MealPlanDetailModal
          isOpen={selectedMealPlanId !== null}
          onClose={() => setSelectedMealPlanId(null)}
          mealPlanId={selectedMealPlanId}
          onAddToGroceryList={handleAddMealPlanToGroceryList}
        />
      )}

      {/* Lightweight toast (no external deps) */}
      {toast && (
        <div className="fixed bottom-4 right-4 z-[60] max-w-sm w-[calc(100vw-2rem)]">
          <div
            className={`rounded-xl shadow-xl border px-4 py-3 bg-white flex items-start gap-3 ${
              toast.type === 'success'
                ? 'border-green-200'
                : toast.type === 'error'
                  ? 'border-red-200'
                  : 'border-sage-200'
            }`}
            role="status"
            aria-live="polite"
          >
            <div className="mt-1">
              {toast.type === 'info' ? (
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-sage-600 border-t-transparent" />
              ) : toast.type === 'success' ? (
                <div className="h-4 w-4 rounded-full bg-green-500" />
              ) : (
                <div className="h-4 w-4 rounded-full bg-red-500" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-sage-800">{toast.message}</p>
              {toast.actionLabel && toast.onAction && (
                <button
                  onClick={() => {
                    toast.onAction?.();
                    setToast(null);
                  }}
                  className="mt-2 text-sm font-medium text-sage-700 hover:text-sage-800 underline underline-offset-2"
                >
                  {toast.actionLabel}
                </button>
              )}
            </div>
            <button
              onClick={() => setToast(null)}
              className="text-sage-500 hover:text-sage-700 rounded-lg p-1"
              aria-label="Dismiss notification"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
