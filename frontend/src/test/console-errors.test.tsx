import { describe, it, expect, vi } from 'vitest'
import { render } from './test-utils'
import { getConsoleErrors, getConsoleWarnings, clearConsoleErrors, clearConsoleWarnings } from './setup'
import App from '../App'

// Mock API services
vi.mock('../services/api', () => ({
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

describe('Console Error Detection', () => {
  it('should track console errors during render', () => {
    clearConsoleErrors()
    
    // Trigger a console error
    console.error('Test error message')
    
    const errors = getConsoleErrors()
    expect(errors).toContain('Test error message')
  })

  it('should track console warnings during render', () => {
    clearConsoleWarnings()
    
    // Trigger a console warning
    console.warn('Test warning message')
    
    const warnings = getConsoleWarnings()
    expect(warnings).toContain('Test warning message')
  })

  it('should detect console errors in component rendering', async () => {
    clearConsoleErrors()
    
    // Component that intentionally causes an error
    const ErrorComponent = () => {
      console.error('Component rendering error')
      return <div>Error Component</div>
    }
    
    render(<ErrorComponent />)
    
    const errors = getConsoleErrors()
    expect(errors).toContain('Component rendering error')
  })

  it('should clear console errors between tests', () => {
    // This test verifies that our setup properly clears errors
    const errors = getConsoleErrors()
    expect(errors).toHaveLength(0)
  })
})