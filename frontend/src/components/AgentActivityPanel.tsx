/**
 * AgentActivityPanel - Shows AI agent activity during meal plan creation.
 * 
 * Displays real-time streaming updates including:
 * - Current agent thinking/processing
 * - Tool invocations and results
 * - Activity log of completed steps
 * - Progressive meal plan preview
 */

import { useState, useEffect, useRef } from 'react';
import type { AgentActivityEvent, ActivityLogItem, MealPlanDayPreview } from '../types';

interface AgentActivityPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (mealPlan: string) => void;
  eventStream: AsyncGenerator<AgentActivityEvent> | null;
  planConfig: {
    days: number;
    people: number;
    dietary_restrictions: string[];
    budget?: number;
  };
}

export function AgentActivityPanel({
  isOpen,
  onClose,
  onComplete,
  eventStream,
  planConfig,
}: AgentActivityPanelProps) {
  const [activityLog, setActivityLog] = useState<ActivityLogItem[]>([]);
  const [currentActivity, setCurrentActivity] = useState<string>('Initializing...');
  const [currentTool, setCurrentTool] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<MealPlanDayPreview[]>([]);
  const [mealPlanResult, setMealPlanResult] = useState<string | null>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Reset state when opening with new stream
  useEffect(() => {
    if (isOpen && eventStream) {
      setActivityLog([]);
      setCurrentActivity('Initializing...');
      setCurrentTool(null);
      setProgress(0);
      setIsComplete(false);
      setError(null);
      setPreview([]);
      setMealPlanResult(null);
    }
  }, [isOpen, eventStream]);

  // Process the event stream
  useEffect(() => {
    if (!eventStream || !isOpen) return;

    let isCancelled = false;

    const processStream = async () => {
      try {
        for await (const event of eventStream) {
          if (isCancelled) break;

          switch (event.type) {
            case 'agent_thinking':
              {
                const content = sanitizeContent(event.content || 'Thinking...');
                if (content) {
                  setCurrentActivity(content);
                  setCurrentTool(null);
                  addToLog({
                    type: 'agent_thinking',
                    content,
                  });
                  incrementProgress(5);
                }
              }
              break;

            case 'tool_start':
              {
                const toolName = event.tool || 'Unknown Tool';
                const inputSummary = sanitizeContent(event.input_summary || '');
                setCurrentTool(toolName);
                setCurrentActivity(inputSummary || `Using ${toolName}...`);
                addToLog({
                  type: 'tool_start',
                  content: `Using ${toolName}${inputSummary ? `: ${inputSummary}` : ''}`,
                });
                incrementProgress(10);
              }
              break;

            case 'tool_result':
              {
                const summary = sanitizeContent(event.summary || 'Completed');
                if (summary) {
                  addToLog({
                    type: 'tool_result',
                    content: `✓ ${event.tool || 'Tool'}: ${summary}`,
                  });
                }
                incrementProgress(10);
              }
              break;

            case 'task_complete':
              {
                setCurrentTool(null);
                const taskName = sanitizeContent(event.task || 'Task');
                const summary = sanitizeContent(event.summary || 'Completed');
                if (taskName || summary) {
                  setCurrentActivity(`Completed: ${taskName || 'Task'}`);
                  addToLog({
                    type: 'task_complete',
                    content: `✓ ${taskName}: ${summary}`,
                  });
                }
                incrementProgress(15);
              }
              break;

            case 'preview_update':
              if (event.preview?.days) {
                setPreview(event.preview.days);
              }
              break;

            case 'complete':
              setProgress(100);
              setIsComplete(true);
              setCurrentActivity('Meal plan created successfully!');
              setCurrentTool(null);
              addToLog({
                type: 'complete',
                content: '✓ Meal plan created successfully!',
              });
              if (event.meal_plan) {
                setMealPlanResult(event.meal_plan);
                // Mark all preview days as complete
                const completedDays = Array.from({ length: planConfig.days }, (_, i) => {
                  const date = new Date();
                  date.setDate(date.getDate() + i);
                  return {
                    date: date.toISOString().split('T')[0],
                    breakfast: 'Planned',
                    lunch: 'Planned',
                    dinner: 'Planned',
                  };
                });
                setPreview(completedDays);
                onComplete(event.meal_plan);
              }
              break;

            case 'error':
              setError(event.content || 'An error occurred');
              addToLog({
                type: 'error',
                content: `⚠ Error: ${event.content}`,
              });
              break;

            case 'done':
              if (!isComplete) {
                setProgress(100);
              }
              break;
          }
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : 'Stream error');
        }
      }
    };

    processStream();

    return () => {
      isCancelled = true;
    };
  }, [eventStream, isOpen, onComplete, isComplete]);

  // Auto-scroll log container
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [activityLog]);

  // Sanitize content to remove raw object representations
  const sanitizeContent = (content: string): string => {
    if (!content) return '';
    
    // Skip entries that are raw object representations
    if (content.includes('<crewai.') || 
        content.includes('object at 0x') ||
        content.includes('AgentFinish(') ||
        content.includes('AgentAction(')) {
      return '';
    }
    
    // Clean up ToolResult representations
    if (content.includes("ToolResult(result=") || content.includes("ToolResult(")) {
      const match = content.match(/ToolResult\(result='([^']+)'/);
      if (match) {
        try {
          const jsonStr = match[1].replace(/\\'/g, "'").replace(/'/g, '"');
          const parsed = JSON.parse(jsonStr);
          return parsed.message || parsed.status || 'Completed';
        } catch {
          // If JSON parse fails, just extract a clean portion
          return 'Tool completed';
        }
      }
      return 'Tool completed';
    }
    
    // Remove JSON-like error structures that are too verbose
    if (content.includes("{'status': 'error'") || content.includes('{"status": "error"')) {
      const msgMatch = content.match(/['"']message['"]:\s*['"']([^'"]+)['"']/);
      if (msgMatch) {
        return msgMatch[1].slice(0, 100);
      }
      return 'Processing error occurred';
    }
    
    // Clean up escaped characters and extra whitespace
    return content
      .replace(/\\n/g, ' ')
      .replace(/\\\\/g, '')
      .replace(/\s+/g, ' ')
      .trim()
      .slice(0, 200);
  };

  const addToLog = ({ type, content }: { type: ActivityLogItem['type']; content: string }) => {
    const sanitized = sanitizeContent(content);
    // Skip empty or unhelpful entries
    if (!sanitized || sanitized.length < 3) {
      return;
    }
    const newItem: ActivityLogItem = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      content: sanitized,
      timestamp: new Date(),
      isActive: false,
    };
    setActivityLog(prev => [...prev, newItem]);
  };

  const incrementProgress = (amount: number) => {
    setProgress(prev => Math.min(prev + amount, 95));
  };

  // Generate preview days
  const getPreviewDays = () => {
    const days: MealPlanDayPreview[] = [];
    const today = new Date();
    for (let i = 0; i < Math.min(planConfig.days, 7); i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      const existing = preview.find(p => p.date === date.toISOString().split('T')[0]);
      days.push({
        date: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
        breakfast: existing?.breakfast || 'pending',
        lunch: existing?.lunch || 'pending',
        dinner: existing?.dinner || 'pending',
      });
    }
    return days;
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      onClick={isComplete ? onClose : undefined}
    >
      <div 
        className="bg-cream-50 rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden shadow-2xl border border-cream-200"
        onClick={(e) => e.stopPropagation()}
        style={{
          animation: 'slideUp 0.3s ease-out',
        }}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-sage-600 to-sage-700 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-display font-bold text-white">
                {isComplete ? 'Meal Plan Ready!' : 'Creating Your Meal Plan'}
              </h2>
              <p className="text-sage-100 text-sm">
                {planConfig.days} days • {planConfig.people} people
                {planConfig.dietary_restrictions.length > 0 && ` • ${planConfig.dietary_restrictions.join(', ')}`}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            disabled={!isComplete && !error}
            title={!isComplete && !error ? 'Please wait for completion' : 'Close'}
          >
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-3 bg-sage-50 border-b border-sage-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-sage-700">Progress</span>
            <span className="text-sm font-bold text-sage-800">{progress}%</span>
          </div>
          <div className="h-2 bg-sage-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-terracotta-400 to-terracotta-500 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Current Activity */}
        <div className="px-6 py-4 border-b border-cream-200">
          <div className="text-xs font-medium text-sage-500 uppercase tracking-wide mb-2">
            Current Activity
          </div>
          <div className="bg-sage-100 rounded-xl p-4 border border-sage-200">
            {currentTool && (
              <div className="flex items-center gap-2 text-terracotta-600 font-medium mb-1">
                <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span className="text-sm">Using: {currentTool}</span>
              </div>
            )}
            <p className="text-sage-700">{currentActivity}</p>
          </div>
        </div>

        {/* Activity Log */}
        <div className="px-6 py-4 border-b border-cream-200">
          <div className="text-xs font-medium text-sage-500 uppercase tracking-wide mb-2">
            Activity Log
          </div>
          <div 
            ref={logContainerRef}
            className="bg-white rounded-xl border border-cream-200 max-h-40 overflow-y-auto"
          >
            {activityLog.length === 0 ? (
              <div className="p-4 text-sage-400 text-sm italic text-center">
                Waiting for agent activity...
              </div>
            ) : (
              <div className="divide-y divide-cream-100">
                {activityLog.map((item, index) => (
                  <div 
                    key={item.id}
                    className="px-4 py-2 text-sm flex items-start gap-2"
                    style={{
                      animation: `fadeSlideIn 0.3s ease-out ${index * 0.05}s both`,
                    }}
                  >
                    <span className={`flex-shrink-0 mt-0.5 ${
                      item.type === 'error' ? 'text-red-500' :
                      item.type === 'complete' ? 'text-green-600' :
                      item.type === 'tool_result' || item.type === 'task_complete' ? 'text-sage-600' :
                      'text-sage-400'
                    }`}>
                      {item.type === 'tool_start' ? '🔧' :
                       item.type === 'agent_thinking' ? '💭' :
                       item.type === 'error' ? '⚠️' :
                       item.type === 'complete' ? '✨' : '→'}
                    </span>
                    <span className={`${
                      item.type === 'error' ? 'text-red-700' :
                      item.type === 'complete' ? 'text-green-700' :
                      'text-sage-700'
                    }`}>
                      {item.content}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Preview */}
        <div className="px-6 py-4">
          <div className="text-xs font-medium text-sage-500 uppercase tracking-wide mb-2">
            Preview {isComplete ? '(Complete!)' : '(building...)'}
          </div>
          <div className="bg-white rounded-xl border border-cream-200 overflow-hidden">
            <div className="grid grid-cols-3 text-xs font-medium text-sage-600 bg-cream-100 border-b border-cream-200">
              <div className="px-3 py-2">Day</div>
              <div className="px-3 py-2">Meals</div>
              <div className="px-3 py-2">Status</div>
            </div>
            <div className="divide-y divide-cream-100 max-h-32 overflow-y-auto">
              {getPreviewDays().map((day, idx) => (
                <div 
                  key={idx} 
                  className="grid grid-cols-3 text-sm py-2"
                  style={{
                    animation: `fadeIn 0.3s ease-out ${idx * 0.1}s both`,
                  }}
                >
                  <div className="px-3 font-medium text-sage-800">{day.date}</div>
                  <div className="px-3 text-sage-600 truncate">
                    {day.breakfast !== 'pending' && day.lunch !== 'pending' && day.dinner !== 'pending' 
                      ? `${day.breakfast?.split(' ').slice(0, 2).join(' ')}...` 
                      : '—'}
                  </div>
                  <div className="px-3">
                    {day.breakfast !== 'pending' && day.lunch !== 'pending' && day.dinner !== 'pending' ? (
                      <span className="inline-flex items-center gap-1 text-green-600">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Ready
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-sage-400">
                        <div className="w-3 h-3 rounded-full border-2 border-sage-300 border-t-sage-500 animate-spin" />
                        Pending
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="px-6 pb-4">
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
              <div className="flex items-center gap-2 font-medium mb-1">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Error
              </div>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Complete State with Meal Plan Result */}
        {isComplete && !error && (
          <div className="px-6 pb-4 space-y-4">
            {mealPlanResult && (
              <div className="bg-sage-50 border border-sage-200 rounded-xl p-4 max-h-48 overflow-y-auto">
                <div className="text-xs font-medium text-sage-500 uppercase tracking-wide mb-2">
                  Your Meal Plan
                </div>
                <div className="text-sm text-sage-700 whitespace-pre-wrap font-mono leading-relaxed">
                  {mealPlanResult.length > 1500 
                    ? mealPlanResult.slice(0, 1500) + '...\n\n(See full plan in your meal plans list)'
                    : mealPlanResult}
                </div>
              </div>
            )}
            <button
              onClick={onClose}
              className="w-full py-3 bg-gradient-to-r from-sage-600 to-sage-700 hover:from-sage-700 hover:to-sage-800 text-white rounded-xl font-medium transition-all shadow-lg hover:shadow-xl"
            >
              Done
            </button>
          </div>
        )}
      </div>

      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes fadeSlideIn {
          from {
            opacity: 0;
            transform: translateX(-10px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}

