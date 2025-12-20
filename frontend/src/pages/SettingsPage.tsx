import { useEffect, useMemo, useState } from 'react';
import { getDefaultPeopleCount, setDefaultPeopleCount, clampInt } from '../services/settings';

export function SettingsPage() {
  const initialPeople = useMemo(() => getDefaultPeopleCount(), []);
  const [people, setPeople] = useState<number>(initialPeople);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    // Keep localStorage in sync when the value changes.
    setDefaultPeopleCount(people);
    setSavedAt(Date.now());
  }, [people]);

  return (
    <div className="min-h-screen bg-cream-50">
      <header className="bg-white border-b border-cream-300 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-display font-bold text-sage-800">Settings</h1>
            <p className="text-sage-600 text-sm mt-1">
              Customize defaults used across the app
            </p>
          </div>
        </div>
      </header>

      <div className="p-6 max-w-3xl">
        <div className="bg-white rounded-xl border border-cream-200 shadow-sm p-6">
          <h2 className="text-lg font-display font-bold text-sage-800 mb-1">Meal planning</h2>
          <p className="text-sm text-sage-600 mb-6">
            This default is used when creating new meal plans.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-sage-700 mb-1">
                Default people
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={people}
                onChange={(e) => {
                  const next = e.target.value ? Number.parseInt(e.target.value, 10) : 2;
                  setPeople(clampInt(Number.isNaN(next) ? 2 : next, 1, 20));
                }}
                className="w-full px-4 py-2.5 bg-white border border-cream-300 rounded-lg text-sage-800 placeholder-sage-400 focus:outline-none focus:ring-2 focus:ring-sage-300"
              />
              <p className="text-xs text-sage-500 mt-2">
                Used for portion sizing and grocery list scaling.
              </p>
            </div>

            <div className="md:text-right">
              <div className="text-xs text-sage-500">
                {savedAt ? 'Saved' : 'Not saved'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

