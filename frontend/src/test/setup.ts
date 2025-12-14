import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Console error tracking for tests
const originalConsoleError = console.error
const originalConsoleWarn = console.warn

let consoleErrors: string[] = []
let consoleWarnings: string[] = []

// Mock console.error and console.warn to capture them
console.error = (...args: any[]) => {
  const message = args.join(' ')
  consoleErrors.push(message)
  // Still call original to see errors in test output
  originalConsoleError(...args)
}

console.warn = (...args: any[]) => {
  const message = args.join(' ')
  consoleWarnings.push(message)
  // Still call original to see warnings in test output
  originalConsoleWarn(...args)
}

// Helper functions to access captured console output
export const getConsoleErrors = () => [...consoleErrors]
export const getConsoleWarnings = () => [...consoleWarnings]
export const clearConsoleErrors = () => { consoleErrors = [] }
export const clearConsoleWarnings = () => { consoleWarnings = [] }

// Reset console tracking before each test
beforeEach(() => {
  clearConsoleErrors()
  clearConsoleWarnings()
})

// Restore original console methods after all tests
afterAll(() => {
  console.error = originalConsoleError
  console.warn = originalConsoleWarn
})

// Mock IntersectionObserver (often needed for modern components)
global.IntersectionObserver = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
}))

// Mock ResizeObserver (often needed for responsive components)
global.ResizeObserver = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
}))

// Mock window.matchMedia (needed for responsive design testing)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})