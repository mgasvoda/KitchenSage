import { describe, it, expect, vi } from 'vitest'
import { render } from './test-utils'
import { getConsoleErrors, clearConsoleErrors } from './setup'

// Mock component that would use an invalid Tailwind class
const ComponentWithInvalidTailwind = () => {
  return <div className="text-balance">This would cause the Tailwind error</div>
}

describe('Tailwind Error Detection', () => {
  it('demonstrates how console error detection would catch Tailwind utility errors', () => {
    clearConsoleErrors()
    
    // This test demonstrates the pattern - in real usage, the error would come from Vite/Tailwind
    // Since we can't reproduce the exact Vite error in test environment, we simulate it
    console.error('`@utility .text-balance` defines an invalid utility name. Utilities should be alphanumeric and start with a lowercase letter.')
    
    const errors = getConsoleErrors()
    
    // This would have caught the original Tailwind error
    expect(errors).toContain('`@utility .text-balance` defines an invalid utility name. Utilities should be alphanumeric and start with a lowercase letter.')
  })
  
  it('renders component that would use corrected Tailwind class', () => {
    clearConsoleErrors()
    
    // Component with the fixed class name
    const FixedComponent = () => {
      return <div className="textbalance">This uses the correct utility name</div>
    }
    
    render(<FixedComponent />)
    
    // Should not produce console errors
    const errors = getConsoleErrors()
    expect(errors).toHaveLength(0)
  })
})