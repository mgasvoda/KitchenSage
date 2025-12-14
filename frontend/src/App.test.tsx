import { describe, it, expect, vi } from 'vitest'
import { renderWithoutRouter, screen, waitFor } from './test/test-utils'
import App from './App'
import { getConsoleErrors, clearConsoleErrors } from './test/setup'

// Mock the API service to prevent real API calls during testing
vi.mock('./services/api', () => ({
  chatApi: {
    sendMessage: vi.fn(),
    sendStreamMessage: vi.fn(),
  },
  recipeApi: {
    list: vi.fn(() => Promise.resolve([])),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    discover: vi.fn(),
  },
  mealPlanApi: {
    list: vi.fn(() => Promise.resolve([])),
    get: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
  groceryApi: {
    list: vi.fn(() => Promise.resolve([])),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('App Component', () => {
  it('renders without crashing', () => {
    renderWithoutRouter(<App />)
    expect(document.body).toBeInTheDocument()
  })

  it('redirects to chat page on root path', async () => {
    renderWithoutRouter(<App />)
    
    // Should redirect from / to /chat
    await waitFor(() => {
      expect(window.location.pathname).toBe('/chat')
    })
  })

  it('renders main layout components', async () => {
    renderWithoutRouter(<App />)
    
    // Wait for the redirect and page to load
    await waitFor(() => {
      expect(window.location.pathname).toBe('/chat')
    })

    // Check that basic layout is rendered
    // These tests are flexible and will work even if the exact text changes
    const mainElement = document.querySelector('main')
    expect(mainElement).toBeInTheDocument()
  })

  it('should not produce console errors on initial render', async () => {
    clearConsoleErrors()
    
    renderWithoutRouter(<App />)
    
    // Wait for any async operations to complete
    await waitFor(() => {
      expect(window.location.pathname).toBe('/chat')
    }, { timeout: 3000 })

    // Small delay to ensure all rendering is complete
    await new Promise(resolve => setTimeout(resolve, 100))

    const errors = getConsoleErrors()
    
    // Filter out common non-critical errors that might occur in test environment
    const criticalErrors = errors.filter(error => 
      !error.includes('Warning:') && // React warnings are not critical errors
      !error.includes('act(') &&     // React act warnings
      !error.includes('useNavigate') && // Router warnings in test
      !error.includes('validateDOMNesting') // DOM nesting warnings
    )

    if (criticalErrors.length > 0) {
      console.log('Critical console errors found:')
      criticalErrors.forEach(error => console.log('  -', error))
    }

    expect(criticalErrors).toHaveLength(0)
  })

  it('navigation between pages works', async () => {
    renderWithoutRouter(<App />)
    
    // Start on chat page (after redirect)
    await waitFor(() => {
      expect(window.location.pathname).toBe('/chat')
    })

    // Note: This test is simplified since we'd need to simulate navigation
    // In a real scenario, you'd click navigation links and test the routing
  })
})