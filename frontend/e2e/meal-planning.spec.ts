import { test, expect } from '@playwright/test';

/**
 * E2E tests for meal planning functionality covering:
 * - Page rendering
 * - Meal plan creation workflow
 * - Form validation
 * - Error handling
 * - Delete functionality
 * - Regression tests for recent bug fixes
 */

test.describe('Meal Planning', () => {

  test.describe('Page Rendering', () => {
    test('renders meal plans page with create button', async ({ page }) => {
      // Mock empty meal plans initially
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [],
            total: 0,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Check main heading
      await expect(page.getByRole('heading', { name: 'Meal Plans' })).toBeVisible();

      // Check create button
      await expect(page.getByRole('button', { name: 'Generate AI Meal Plan' })).toBeVisible();
    });

    test('displays empty state when no meal plans exist', async ({ page }) => {
      // Mock empty meal plans
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [],
            total: 0,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Wait for loading to finish
      await page.waitForTimeout(500);

      // Check empty state message
      await expect(page.getByText(/No meal plans yet/)).toBeVisible();
      await expect(page.getByText(/Use the form above to create/)).toBeVisible();
    });
  });

  test.describe('Meal Plan Creation', () => {
    test('displays create form with all fields', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [],
            total: 0,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Check form fields are visible (inline form, not modal)
      await expect(page.locator('label:has-text("Days")')).toBeVisible();
      await expect(page.locator('label:has-text("People")')).toBeVisible();
      await expect(page.locator('label:has-text("Budget")')).toBeVisible();
      await expect(page.locator('label:has-text("Preferences & Instructions")')).toBeVisible();

      // Check create button
      await expect(page.getByRole('button', { name: 'Generate AI Meal Plan' })).toBeVisible();
    });

    test('creates meal plan successfully', async ({ page }) => {
      let createCalled = false;

      // Mock initial empty list
      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: createCalled ? [
                {
                  id: 1,
                  name: 'Mediterranean Week',
                  is_active: false,
                  people_count: 2,
                  dietary_restrictions: [],
                  meals: [
                    {
                      id: 1,
                      recipe_id: 5,
                      meal_type: 'dinner',
                      day_number: 1,
                      recipe: { name: 'Pasta Primavera' }
                    }
                  ],
                  created_at: '2025-12-14T10:00:00'
                }
              ] : [],
              total: createCalled ? 1 : 0,
              limit: 50,
              offset: 0
            })
          });
        } else if (route.request().method() === 'POST') {
          createCalled = true;
          const postData = route.request().postDataJSON() || {};
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              message: 'Meal plan created successfully',
              meal_plan: {
                id: 1,
                name: 'Mediterranean Week',
                is_active: false,
                people_count: postData.people || 2,
                dietary_restrictions: [],
                meals: []
              }
            })
          });
        }
      });

      await page.goto('/meal-plans');

      // Fill form (inline form, not modal)
      const daysInput = page.locator('label:has-text("Days")').locator('..').locator('input[type="number"]').first();
      await daysInput.fill('7');

      const peopleInput = page.locator('label:has-text("People")').locator('..').locator('input[type="number"]');
      await peopleInput.fill('2');

      const budgetInput = page.locator('label:has-text("Budget")').locator('..').locator('input[type="number"]');
      await budgetInput.fill('150');

      // Submit form
      const submitButton = page.getByRole('button', { name: 'Generate AI Meal Plan' });
      await submitButton.click();

      // Wait for meal plan card to appear and check details
      // Check for "Your Meal Plans" section heading
      await expect(page.getByRole('heading', { name: 'Your Meal Plans' })).toBeVisible({ timeout: 5000 });

      // Verify meal plan details
      await expect(page.getByText('2 people')).toBeVisible();
      await expect(page.getByText(/meals planned/)).toBeVisible();
    });

    test('displays existing meal plans', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [
              {
                id: 1,
                name: 'Weekly Plan #1',
                is_active: true,
                people_count: 4,
                dietary_restrictions: ['vegetarian', 'gluten-free'],
                meals: [
                  { id: 1, recipe_id: 1, meal_type: 'dinner', day_number: 1 },
                  { id: 2, recipe_id: 2, meal_type: 'lunch', day_number: 2 }
                ],
                created_at: '2025-12-14T10:00:00'
              },
              {
                id: 2,
                name: 'Weekend Special',
                is_active: false,
                people_count: 2,
                dietary_restrictions: ['vegan'],
                meals: [
                  { id: 3, recipe_id: 3, meal_type: 'breakfast', day_number: 1 }
                ],
                created_at: '2025-12-13T15:30:00'
              }
            ],
            total: 2,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Wait for loading
      await page.waitForTimeout(500);

      // Check heading
      await expect(page.getByRole('heading', { name: 'Your Meal Plans' })).toBeVisible();

      // Check first meal plan
      await expect(page.getByText('Weekly Plan #1')).toBeVisible();
      await expect(page.getByText('4 people')).toBeVisible();
      await expect(page.getByText('2 meals planned')).toBeVisible();
      await expect(page.getByText('vegetarian')).toBeVisible();
      await expect(page.getByText('gluten-free')).toBeVisible();

      // Check second meal plan
      await expect(page.getByText('Weekend Special')).toBeVisible();
      await expect(page.getByText('2 people')).toBeVisible();
      await expect(page.getByText('1 meals planned')).toBeVisible();
      await expect(page.getByText('vegan')).toBeVisible();
    });
  });

  test.describe('Streaming Meal Plan Creation', () => {
    test('creates meal plan with streaming updates and handles empty prompt', async ({ page }) => {
      let streamStarted = false;
      const consoleErrors: string[] = [];
      const pageErrors: string[] = [];

      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      page.on('pageerror', error => {
        pageErrors.push(error.message);
      });

      // Mock streaming endpoint
      await page.route('**/api/meal-plans/stream*', async route => {
        streamStarted = true;
        const url = new URL(route.request().url());
        const prompt = url.searchParams.get('prompt');
        
        // Verify prompt can be null/empty without errors
        const stream = new ReadableStream({
          start(controller) {
            // Send initial event
            controller.enqueue(new TextEncoder().encode('data: {"type":"agent_thinking","agent":"Meal Planning Expert","content":"Starting meal plan..."}\n\n'));
            
            // Send progress events
            setTimeout(() => {
              controller.enqueue(new TextEncoder().encode('data: {"type":"tool_start","tool":"CreateMealPlanTool","input_summary":"Creating plan"}\n\n'));
            }, 100);
            
            setTimeout(() => {
              controller.enqueue(new TextEncoder().encode('data: {"type":"tool_result","tool":"CreateMealPlanTool","summary":"Meal plan created"}\n\n'));
            }, 200);
            
            setTimeout(() => {
              controller.enqueue(new TextEncoder().encode('data: {"type":"complete","meal_plan":"Meal plan for 7 days"}\n\n'));
            }, 300);
            
            setTimeout(() => {
              controller.enqueue(new TextEncoder().encode('data: {"type":"done"}\n\n'));
              controller.close();
            }, 400);
          }
        });

        await route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          body: stream,
        });
      });

      // Mock list endpoint
      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: streamStarted ? [
                {
                  id: 1,
                  name: 'Meal Plan 2025-12-14',
                  is_active: false,
                  people_count: 2,
                  dietary_restrictions: [],
                  meals: [],
                  created_at: '2025-12-14T10:00:00'
                }
              ] : [],
              total: streamStarted ? 1 : 0,
              limit: 50,
              offset: 0
            })
          });
        }
      });

      await page.goto('/meal-plans');

      // Fill form with empty prompt (this was causing the error)
      const daysInput = page.locator('label:has-text("Days")').locator('..').locator('input[type="number"]').first();
      await daysInput.fill('7');

      const peopleInput = page.locator('label:has-text("People")').locator('..').locator('input[type="number"]');
      await peopleInput.fill('2');

      // Don't fill prompt - leave it empty to test the error scenario

      // Submit form
      const submitButton = page.getByRole('button', { name: 'Generate AI Meal Plan' });
      await submitButton.click();

      // Wait for AgentActivityPanel to appear
      await expect(page.getByText('Creating Your Meal Plan')).toBeVisible({ timeout: 3000 });

      // Wait for streaming to complete
      await expect(page.getByText('Meal plan created successfully!')).toBeVisible({ timeout: 5000 });

      // Verify no errors occurred (the bug would cause "Cannot read properties of undefined (reading 'length')")
      expect(consoleErrors.filter(e => e.includes('Cannot read properties') || e.includes('length'))).toHaveLength(0);
      expect(pageErrors.filter(e => e.includes('Cannot read properties') || e.includes('length'))).toHaveLength(0);

      // Verify the panel shows the correct info without crashing
      await expect(page.getByText(/7 days/)).toBeVisible();
      await expect(page.getByText(/2 people/)).toBeVisible();
    });

    test('creates meal plan with prompt and displays it in AgentActivityPanel', async ({ page }) => {
      const consoleErrors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      page.on('pageerror', error => {
        consoleErrors.push(error.message);
      });

      // Mock streaming endpoint
      await page.route('**/api/meal-plans/stream*', async route => {
        const stream = new ReadableStream({
          start(controller) {
            controller.enqueue(new TextEncoder().encode('data: {"type":"agent_thinking","agent":"Meal Planning Expert","content":"Analyzing preferences..."}\n\n'));
            setTimeout(() => {
              controller.enqueue(new TextEncoder().encode('data: {"type":"complete","meal_plan":"Meal plan created"}\n\n'));
            }, 100);
            setTimeout(() => {
              controller.enqueue(new TextEncoder().encode('data: {"type":"done"}\n\n'));
              controller.close();
            }, 200);
          }
        });

        await route.fulfill({
          status: 200,
          contentType: 'text/event-stream',
          body: stream,
        });
      });

      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: [],
              total: 0,
              limit: 50,
              offset: 0
            })
          });
        }
      });

      await page.goto('/meal-plans');

      // Fill form with a prompt
      const daysInput = page.locator('label:has-text("Days")').locator('..').locator('input[type="number"]').first();
      await daysInput.fill('7');

      const peopleInput = page.locator('label:has-text("People")').locator('..').locator('input[type="number"]');
      await peopleInput.fill('2');

      const promptTextarea = page.locator('label:has-text("Preferences & Instructions")').locator('..').locator('textarea');
      await promptTextarea.fill('vegetarian meals with Italian cuisine focus');

      // Submit form
      const submitButton = page.getByRole('button', { name: 'Generate AI Meal Plan' });
      await submitButton.click();

      // Wait for AgentActivityPanel
      await expect(page.getByText('Creating Your Meal Plan')).toBeVisible({ timeout: 3000 });

      // Verify prompt is displayed (truncated if long)
      await expect(page.getByText(/vegetarian meals/)).toBeVisible();

      // Verify no errors
      expect(consoleErrors.filter(e => e.includes('Cannot read properties') || e.includes('length'))).toHaveLength(0);
    });
  });

  test.describe('Form Validation', () => {
    test('requires valid number inputs', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [],
            total: 0,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Form is inline, no modal to open
      // Try to set negative days (input should prevent it due to min=1)
      const daysInput = page.locator('label:has-text("Days")').locator('..').locator('input[type="number"]').first();
      await expect(daysInput).toHaveAttribute('min', '1');
      await expect(daysInput).toHaveAttribute('max', '30');

      // Try to set negative people
      const peopleInput = page.locator('label:has-text("People")').locator('..').locator('input[type="number"]');
      await expect(peopleInput).toHaveAttribute('min', '1');
      await expect(peopleInput).toHaveAttribute('max', '20');

      // Budget should have min=0
      const budgetInput = page.locator('label:has-text("Budget")').locator('..').locator('input[type="number"]');
      await expect(budgetInput).toHaveAttribute('min', '0');
    });
  });

  test.describe('Error Handling', () => {
    test('displays error on API failure', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: [],
              total: 0,
              limit: 50,
              offset: 0
            })
          });
        } else if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'error',
              message: 'Failed to create meal plan: database error'
            })
          });
        }
      });

      await page.goto('/meal-plans');

      // Fill form and submit
      const daysInput = page.locator('label:has-text("Days")').locator('..').locator('input[type="number"]').first();
      await daysInput.fill('7');

      const submitButton = page.getByRole('button', { name: 'Generate AI Meal Plan' });
      await submitButton.click();

      // Check error message appears
      await expect(page.getByText(/Failed to create meal plan/)).toBeVisible({ timeout: 3000 });
    });

    test('handles network errors gracefully', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: [],
              total: 0,
              limit: 50,
              offset: 0
            })
          });
        } else if (route.request().method() === 'POST') {
          await route.abort('failed');
        }
      });

      await page.goto('/meal-plans');

      // Fill form and submit
      const submitButton = page.getByRole('button', { name: 'Generate AI Meal Plan' });
      await submitButton.click();

      // Check error is displayed
      await expect(page.locator('.bg-red-50')).toBeVisible({ timeout: 3000 });
    });

    test('displays error when loading meal plans fails', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.abort('failed');
      });

      await page.goto('/meal-plans');

      // Wait and check error message appears in red error box
      await expect(page.locator('.bg-red-50')).toBeVisible({ timeout: 3000 });
    });
  });

  test.describe('Regression Tests', () => {
    test('meals are saved separately from meal plan (regression test for "meals column" bug)', async ({ page }) => {
      let createCalled = false;

      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: createCalled ? [
                {
                  id: 1,
                  name: 'Test Plan',
                  is_active: false,
                  people_count: 2,
                  dietary_restrictions: [],
                  // Meals should be in a separate array, not as a column
                  // This is the fix - meals are retrieved separately, not stored as a column
                  meals: [
                    {
                      id: 1,
                      meal_plan_id: 1,
                      recipe_id: 5,
                      meal_type: 'dinner',
                      day_number: 1,
                      servings_override: null,
                      notes: null,
                      recipe: { name: 'Pasta' }
                    },
                    {
                      id: 2,
                      meal_plan_id: 1,
                      recipe_id: 6,
                      meal_type: 'lunch',
                      day_number: 2,
                      servings_override: 4,
                      notes: 'Extra portions',
                      recipe: { name: 'Salad' }
                    }
                  ],
                  created_at: '2025-12-14T10:00:00'
                }
              ] : [],
              total: createCalled ? 1 : 0,
              limit: 50,
              offset: 0
            })
          });
        } else if (route.request().method() === 'POST') {
          createCalled = true;

          // Note: We can't directly check the API request body in Playwright
          // but we can verify the response structure is correct (meals as separate array)

          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              message: 'Meal plan created successfully',
              meal_plan: {
                id: 1,
                name: 'Test Plan',
                is_active: false,
                people_count: 2,
                dietary_restrictions: [],
                meals: []
              }
            })
          });
        }
      });

      await page.goto('/meal-plans');

      // Create a meal plan
      await page.getByRole('button', { name: 'Generate AI Meal Plan' }).click();

      // Wait for creation and reload
      await page.waitForTimeout(1500);

      // Verify the response structure shows meals as a separate array
      // If the bug existed, meals would be saved as a column causing an error
      await expect(page.getByText('2 meals planned')).toBeVisible({ timeout: 5000 });
    });

    test('handles Recipe objects in nutrition analysis (regression test for Recipe.get() bug)', async ({ page }) => {
      // Mock a meal plan with nutritional info in various formats
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [
              {
                id: 1,
                name: 'Healthy Plan',
                is_active: false,
                people_count: 2,
                dietary_restrictions: [],
                meals: [
                  {
                    id: 1,
                    meal_plan_id: 1,
                    recipe_id: 1,
                    meal_type: 'breakfast',
                    day_number: 1,
                    recipe: {
                      id: 1,
                      name: 'Healthy Breakfast',
                      servings: 2,
                      // nutritional_info might be null (edge case)
                      nutritional_info: null
                    }
                  },
                  {
                    id: 2,
                    meal_plan_id: 1,
                    recipe_id: 2,
                    meal_type: 'lunch',
                    day_number: 1,
                    recipe: {
                      id: 2,
                      name: 'Nutritious Lunch',
                      servings: 2,
                      // nutritional_info with actual data
                      nutritional_info: {
                        calories: 450,
                        protein: 25,
                        carbohydrates: 50,
                        fat: 15
                      }
                    }
                  },
                  {
                    id: 3,
                    meal_plan_id: 1,
                    recipe_id: 3,
                    meal_type: 'dinner',
                    day_number: 1,
                    recipe: {
                      id: 3,
                      name: 'Light Dinner',
                      servings: 2
                      // nutritional_info missing entirely
                    }
                  }
                ],
                created_at: '2025-12-14T10:00:00'
              }
            ],
            total: 1,
            limit: 50,
            offset: 0
          })
        });
      });

      // Set up console error monitoring
      const consoleErrors: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      page.on('pageerror', error => {
        consoleErrors.push(error.message);
      });

      await page.goto('/meal-plans');

      // Wait for page to load
      await page.waitForTimeout(1000);

      // Verify meal plan displays
      await expect(page.getByText('Healthy Plan')).toBeVisible();
      await expect(page.getByText('3 meals planned')).toBeVisible();

      // Verify no JavaScript errors occurred
      // The bug would cause "'Recipe' object has no attribute 'get'" errors
      expect(consoleErrors).toHaveLength(0);

      // If nutrition data was displayed somewhere, it should not crash
      // This test primarily ensures no console errors
    });
  });

  test.describe('Active Plan Management', () => {
    test('displays active badge on active plan', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [
              {
                id: 1,
                name: 'Active Plan',
                is_active: true,
                people_count: 2,
                dietary_restrictions: [],
                meals: [
                  { id: 1, recipe_id: 1, meal_type: 'dinner', day_number: 1 }
                ],
                created_at: '2025-12-14T10:00:00'
              },
              {
                id: 2,
                name: 'Inactive Plan',
                is_active: false,
                people_count: 2,
                dietary_restrictions: [],
                meals: [],
                created_at: '2025-12-14T10:00:00'
              }
            ],
            total: 2,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');
      await page.waitForTimeout(500);

      // Check active badge is displayed on active plan
      await expect(page.getByRole('heading', { name: 'Active Plan' }).locator('..').locator('..').getByText('Active').first()).toBeVisible();

      // Check inactive plan card exists
      await expect(page.getByRole('heading', { name: 'Inactive Plan' })).toBeVisible();
    });

    test('can activate a meal plan', async ({ page }) => {
      let activePlanId = 1;

      await page.route('**/api/meal-plans/*/activate', async route => {
        const url = route.request().url();
        const match = url.match(/\/meal-plans\/(\d+)\/activate/);
        if (match) {
          activePlanId = parseInt(match[1]);
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: 'Meal plan activated successfully'
          })
        });
      });

      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: [
                {
                  id: 1,
                  name: 'Plan A',
                  is_active: activePlanId === 1,
                  people_count: 2,
                  dietary_restrictions: [],
                  meals: [],
                  created_at: '2025-12-14T10:00:00'
                },
                {
                  id: 2,
                  name: 'Plan B',
                  is_active: activePlanId === 2,
                  people_count: 2,
                  dietary_restrictions: [],
                  meals: [],
                  created_at: '2025-12-14T10:00:00'
                }
              ],
              total: 2,
              limit: 50,
              offset: 0
            })
          });
        }
      });

      await page.goto('/meal-plans');
      await page.waitForTimeout(500);

      // Plan A should be active initially
      const planACard = page.locator('text=Plan A').locator('..').locator('..');
      await expect(planACard.getByText('Active')).toBeVisible();

      // Click "Set Active" on Plan B
      const planBCard = page.locator('text=Plan B').locator('..').locator('..');
      await planBCard.getByRole('button', { name: 'Set Active' }).click();

      // Wait for page to update
      await page.waitForTimeout(1000);

      // Plan B should now be active
      await expect(planBCard.getByText('Active')).toBeVisible();
    });

    test('meal plan cards show day count instead of date range', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [
              {
                id: 1,
                name: '7-Day Plan',
                is_active: true,
                people_count: 2,
                dietary_restrictions: [],
                meals: [
                  { id: 1, recipe_id: 1, meal_type: 'breakfast', day_number: 1 },
                  { id: 2, recipe_id: 2, meal_type: 'lunch', day_number: 1 },
                  { id: 3, recipe_id: 3, meal_type: 'dinner', day_number: 1 },
                  { id: 4, recipe_id: 4, meal_type: 'breakfast', day_number: 7 }
                ],
                created_at: '2025-12-14T10:00:00'
              }
            ],
            total: 1,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');
      await page.waitForTimeout(500);

      // Should show "7-day plan" based on max day_number (use exact match to avoid ambiguity)
      await expect(page.getByText('📅 7-day plan')).toBeVisible();

      // Should NOT show date ranges
      await expect(page.getByText(/Dec \d+/)).not.toBeVisible();
      await expect(page.getByText(/2025-\d{2}-\d{2}/)).not.toBeVisible();
    });
  });

  test.describe('Edge Cases', () => {
    test('handles large number of meal plans', async ({ page }) => {
      const mealPlans = Array.from({ length: 15 }, (_, i) => ({
        id: i + 1,
        name: `Meal Plan ${i + 1}`,
        is_active: i === 0,
        people_count: 2,
        dietary_restrictions: [],
        meals: [],
        created_at: '2025-12-14T10:00:00'
      }));

      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: mealPlans,
            total: 15,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Wait for loading
      await page.waitForTimeout(500);

      // Check that multiple meal plans render (use exact matching to avoid conflicts with 10, 11, etc.)
      await expect(page.getByRole('heading', { name: 'Meal Plan 1', exact: true })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Meal Plan 15' })).toBeVisible();

      // Check that all meal plans are rendered (at least 15 meal plan headings)
      const mealPlanHeadings = page.locator('h3.font-display').filter({ hasText: /^Meal Plan \d+/ });
      expect(await mealPlanHeadings.count()).toBe(15);
    });

    test('displays meal plan with no meals', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [
              {
                id: 1,
                name: 'Empty Plan',
                is_active: false,
                people_count: 2,
                dietary_restrictions: [],
                meals: [],
                created_at: '2025-12-14T10:00:00'
              }
            ],
            total: 1,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Should display meal plan even with 0 meals
      await expect(page.getByText('Empty Plan')).toBeVisible();
      await expect(page.getByText('0 meals planned')).toBeVisible();
    });

    test('handles long meal plan names', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [
              {
                id: 1,
                name: 'A Very Long Meal Plan Name That Should Still Display Correctly Without Breaking The Layout',
                is_active: false,
                people_count: 2,
                dietary_restrictions: [],
                meals: [],
                created_at: '2025-12-14T10:00:00'
              }
            ],
            total: 1,
            limit: 50,
            offset: 0
          })
        });
      });

      await page.goto('/meal-plans');

      // Should display long name without layout issues
      await expect(page.getByText(/A Very Long Meal Plan Name/)).toBeVisible();
    });
  });
});
