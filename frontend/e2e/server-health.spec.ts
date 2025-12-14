import { test, expect } from '@playwright/test'

/**
 * These tests check the Vite dev server health without needing browser rendering.
 * They help catch build/compilation errors like Tailwind CSS issues.
 */
test.describe('Server Health Checks', () => {
  test('index.css should load without server errors', async ({ request }) => {
    // This test catches Vite/Tailwind build errors that return 500 status
    const response = await request.get('/src/index.css')
    
    if (response.status() >= 400) {
      const body = await response.text()
      console.log('CSS Load Error Details:')
      console.log(`  Status: ${response.status()}`)
      console.log(`  Body: ${body.substring(0, 500)}...`)
    }
    
    expect(response.status(), 'Expected index.css to load without server errors').toBeLessThan(400)
  })

  test('main.tsx should load without server errors', async ({ request }) => {
    const response = await request.get('/src/main.tsx')
    
    if (response.status() >= 400) {
      const body = await response.text()
      console.log('Main.tsx Load Error Details:')
      console.log(`  Status: ${response.status()}`)
      console.log(`  Body: ${body.substring(0, 500)}...`)
    }
    
    expect(response.status(), 'Expected main.tsx to load without server errors').toBeLessThan(400)
  })

  test('App.tsx should load without server errors', async ({ request }) => {
    const response = await request.get('/src/App.tsx')
    
    if (response.status() >= 400) {
      const body = await response.text()
      console.log('App.tsx Load Error Details:')
      console.log(`  Status: ${response.status()}`)
      console.log(`  Body: ${body.substring(0, 500)}...`)
    }
    
    expect(response.status(), 'Expected App.tsx to load without server errors').toBeLessThan(400)
  })

  test('home page HTML should load successfully', async ({ request }) => {
    const response = await request.get('/')
    
    expect(response.status(), 'Expected home page to load successfully').toBe(200)
    
    const html = await response.text()
    expect(html.toLowerCase()).toContain('<!doctype html>')
    expect(html).toContain('<div id="root">')
  })
})

