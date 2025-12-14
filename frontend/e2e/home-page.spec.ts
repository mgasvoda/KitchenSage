import { test, expect } from '@playwright/test'

test.describe('Home Page Load', () => {
  test('should load home page without console errors', async ({ page }) => {
    const consoleErrors: string[] = []
    const consoleWarnings: string[] = []

    // Listen for console messages before navigating
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(msg.text())
      }
    })

    // Listen for page errors (uncaught exceptions)
    page.on('pageerror', (error) => {
      consoleErrors.push(`Page Error: ${error.message}`)
    })

    // Navigate to the home page
    const response = await page.goto('/')

    // Wait for the page to fully load
    await page.waitForLoadState('networkidle')

    // Log any captured errors/warnings for debugging
    if (consoleErrors.length > 0) {
      console.log('Console Errors captured:')
      consoleErrors.forEach((error) => console.log(`  - ${error}`))
    }

    if (consoleWarnings.length > 0) {
      console.log('Console Warnings captured:')
      consoleWarnings.forEach((warning) => console.log(`  - ${warning}`))
    }

    // Assert no console errors occurred
    expect(consoleErrors, 'Expected no console errors on page load').toHaveLength(0)

    // Verify the page loaded successfully (status 200)
    expect(response?.status()).toBe(200)
  })

  test('should load the page and render main content', async ({ page }) => {
    const consoleErrors: string[] = []

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text())
      }
    })

    page.on('pageerror', (error) => {
      consoleErrors.push(`Page Error: ${error.message}`)
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Verify basic page structure exists
    const mainElement = page.locator('main')
    await expect(mainElement).toBeVisible()

    // Report any errors found
    if (consoleErrors.length > 0) {
      console.log('Console Errors during render:')
      consoleErrors.forEach((error) => console.log(`  - ${error}`))
    }

    expect(consoleErrors, 'Expected no console errors during page render').toHaveLength(0)
  })

  test('should have no failed network requests on page load', async ({ page }) => {
    const failedRequests: string[] = []
    const serverErrors: { url: string; status: number }[] = []

    // Track requests that fail completely
    page.on('requestfailed', (request) => {
      failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText}`)
    })

    // Track responses with 4xx/5xx status codes
    page.on('response', (response) => {
      const status = response.status()
      if (status >= 400) {
        serverErrors.push({ url: response.url(), status })
      }
    })

    await page.goto('/')
    await page.waitForLoadState('networkidle')

    if (failedRequests.length > 0) {
      console.log('Failed Network Requests:')
      failedRequests.forEach((req) => console.log(`  - ${req}`))
    }

    if (serverErrors.length > 0) {
      console.log('Server Error Responses (4xx/5xx):')
      serverErrors.forEach((err) => console.log(`  - ${err.status} ${err.url}`))
    }

    expect(failedRequests, 'Expected no failed network requests on page load').toHaveLength(0)
    expect(serverErrors, 'Expected no server error responses (4xx/5xx) on page load').toHaveLength(0)
  })
})

