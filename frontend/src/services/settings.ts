const DEFAULT_PEOPLE_STORAGE_KEY = 'kitchensage.default_people';

export function clampInt(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, Math.trunc(value)));
}

export function getDefaultPeopleCount(): number {
  try {
    const raw = window.localStorage.getItem(DEFAULT_PEOPLE_STORAGE_KEY);
    if (!raw) return 2;
    const parsed = Number.parseInt(raw, 10);
    if (Number.isNaN(parsed)) return 2;
    return clampInt(parsed, 1, 20);
  } catch {
    return 2;
  }
}

export function setDefaultPeopleCount(people: number): void {
  try {
    const value = clampInt(people, 1, 20);
    window.localStorage.setItem(DEFAULT_PEOPLE_STORAGE_KEY, String(value));
  } catch {
    // Ignore storage errors (private mode, disabled storage, etc.)
  }
}

