import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

// Custom render function that includes common providers for isolated component testing
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <MemoryRouter>
      {children}
    </MemoryRouter>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

// Export both custom render and a render function without router for full app testing
export * from '@testing-library/react'
export { customRender as render }

// For testing full App component which already has its own router
export const renderWithoutRouter = (
  ui: ReactElement,
  options?: RenderOptions,
) => render(ui, options)