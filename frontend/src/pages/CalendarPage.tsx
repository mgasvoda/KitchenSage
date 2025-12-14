import { useState, useEffect, useRef } from 'react';
import { mealPlanApi } from '../services/api';
import { AgentActivityPanel } from '../components/AgentActivityPanel';
import { MealPlanDetailModal } from '../components/MealPlanDetailModal';
import type { MealPlan, AgentActivityEvent } from '../types';

export function CalendarPage() {
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreatePanel, setShowCreatePanel] = useState(false);
  const [eventStream, setEventStream] = useState<AsyncGenerator<AgentActivityEvent> | null>(null);
  const [createForm, setCreateForm] = useState({
    days: 7,
    people: 2,
    dietary_restrictions: [] as string[],
    budget: undefined as number | undefined,
  });
  const [dietaryInput, setDietaryInput] = useState('');
  const [selectedMealPlanId, setSelectedMealPlanId] = useState<number | null>(null);
  const streamRef = useRef<AsyncGenerator<AgentActivityEvent> | null>(null);

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
    const stream = mealPlanApi.streamCreate(createForm);
    streamRef.current = stream;
    setEventStream(stream);
    setShowCreatePanel(true);
  };

  const handlePanelComplete = async (mealPlan: string) => {
    // Reload meal plans after completion
    await loadMealPlans();
    setCreateForm({ days: 7, people: 2, dietary_restrictions: [], budget: undefined });
    setDietaryInput('');
  };

  const handlePanelClose = () => {
    setShowCreatePanel(false);
    setEventStream(null);
    streamRef.current = null;
  };

  const addDietaryRestriction = () => {
    const trimmed = dietaryInput.trim();
    if (trimmed && !createForm.dietary_restrictions.includes(trimmed)) {
      setCreateForm({
        ...createForm,
        dietary_restrictions: [...createForm.dietary_restrictions, trimmed],
      });
      setDietaryInput('');
    }
  };

  const removeDietaryRestriction = (restriction: string) => {
    setCreateForm({
      ...createForm,
      dietary_restrictions: createForm.dietary_restrictions.filter(r => r !== restriction),
    });
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

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-sage-100 mb-1">
                Days
              </label>
              <input
                type="number"
                min={1}
                max={30}
                value={createForm.days}
                onChange={(e) => setCreateForm({ ...createForm, days: parseInt(e.target.value) || 7 })}
                className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white placeholder-sage-200 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-sage-100 mb-1">
                People
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={createForm.people}
                onChange={(e) => setCreateForm({ ...createForm, people: parseInt(e.target.value) || 2 })}
                className="w-full px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white placeholder-sage-200 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
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

          {/* Dietary Restrictions */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-sage-100 mb-2">
              Dietary Restrictions
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={dietaryInput}
                onChange={(e) => setDietaryInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addDietaryRestriction())}
                placeholder="e.g., vegetarian, gluten-free"
                className="flex-1 px-4 py-2.5 bg-white/10 border border-white/20 rounded-lg text-white placeholder-sage-300 focus:outline-none focus:ring-2 focus:ring-white/30"
              />
              <button
                type="button"
                onClick={addDietaryRestriction}
                className="px-4 py-2.5 bg-white/20 hover:bg-white/30 rounded-lg font-medium transition-colors"
              >
                Add
              </button>
            </div>
            {createForm.dietary_restrictions.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {createForm.dietary_restrictions.map((restriction) => (
                  <span
                    key={restriction}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-white/20 rounded-full text-sm"
                  >
                    {restriction}
                    <button
                      onClick={() => removeDietaryRestriction(restriction)}
                      className="ml-1 hover:text-terracotta-200"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
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
                  className="bg-white rounded-xl shadow-sm border border-cream-200 p-6 hover:shadow-lg transition-all hover:border-sage-300 cursor-pointer"
                  onClick={() => setSelectedMealPlanId(plan.id)}
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
                          {tag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="mt-4 pt-4 border-t border-cream-200">
                    <button className="text-sage-600 hover:text-sage-700 text-sm font-medium flex items-center gap-1">
                      View Details
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
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
        planConfig={createForm}
      />

      {/* Meal Plan Detail Modal */}
      {selectedMealPlanId && (
        <MealPlanDetailModal
          isOpen={selectedMealPlanId !== null}
          onClose={() => setSelectedMealPlanId(null)}
          mealPlanId={selectedMealPlanId}
        />
      )}
    </div>
  );
}
