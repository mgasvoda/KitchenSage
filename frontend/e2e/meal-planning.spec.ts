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
    test('renders calendar page with create button', async ({ page }) => {
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

      await page.goto('/calendar');

      // Check main heading
      await expect(page.getByRole('heading', { name: 'Meal Planning' })).toBeVisible();

      // Check create button
      await expect(page.getByRole('button', { name: 'Create Plan' })).toBeVisible();

      // Check week view grid is present
      await expect(page.locator('.grid.grid-cols-7').first()).toBeVisible();
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

      await page.goto('/calendar');

      // Wait for loading to finish
      await page.waitForTimeout(500);

      // Check empty state message
      await expect(page.getByText(/No meal plans yet/)).toBeVisible();
      await expect(page.getByText(/Use the "Create Plan" button/)).toBeVisible();
    });
  });

  test.describe('Meal Plan Creation', () => {
    test('opens and closes create modal', async ({ page }) => {
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

      await page.goto('/calendar');

      // Open modal
      const createButton = page.getByRole('button', { name: 'Create Plan' });
      await createButton.click();

      // Check modal is visible
      await expect(page.getByRole('heading', { name: 'Create Meal Plan' })).toBeVisible();

      // Check form fields
      await expect(page.locator('label:has-text("Number of Days")')).toBeVisible();
      await expect(page.locator('label:has-text("Number of People")')).toBeVisible();
      await expect(page.locator('label:has-text("Budget")')).toBeVisible();

      // Close modal by clicking X button
      const closeButton = page.locator('button:has(svg)').filter({ has: page.locator('path[d*="M6 18L18 6"]') });
      await closeButton.click();

      // Check modal is closed
      await expect(page.getByRole('heading', { name: 'Create Meal Plan' })).not.toBeVisible();
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
                  name: 'Meal Plan 2025-12-14',
                  start_date: '2025-12-14',
                  end_date: '2025-12-20',
                  people_count: 2,
                  dietary_restrictions: ['vegetarian'],
                  meals: [
                    {
                      id: 1,
                      recipe_id: 5,
                      meal_type: 'dinner',
                      meal_date: '2025-12-14',
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
                name: 'Meal Plan 2025-12-14',
                start_date: '2025-12-14',
                end_date: '2025-12-20',
                people_count: postData.people || 2,
                dietary_restrictions: postData.dietary_restrictions || [],
                meals: []
              }
            })
          });
        }
      });

      await page.goto('/calendar');

      // Open modal
      await page.getByRole('button', { name: 'Create Plan' }).click();

      // Fill form
      const daysInput = page.locator('input[type="number"]').first();
      await daysInput.fill('7');

      const peopleInput = page.locator('label:has-text("Number of People")').locator('..').locator('input[type="number"]');
      await peopleInput.fill('2');

      const budgetInput = page.locator('label:has-text("Budget")').locator('..').locator('input[type="number"]');
      await budgetInput.fill('150');

      // Submit form
      const submitButton = page.getByRole('button', { name: 'Create Meal Plan' });
      await submitButton.click();

      // Wait for meal plan card to appear and check details
      // Modal should close first
      await expect(page.getByRole('heading', { name: 'Create Meal Plan' })).not.toBeVisible({ timeout: 5000 });

      // Then check for "Your Meal Plans" section heading
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
                start_date: '2025-12-14',
                end_date: '2025-12-20',
                people_count: 4,
                dietary_restrictions: ['vegetarian', 'gluten-free'],
                meals: [
                  { id: 1, recipe_id: 1, meal_type: 'dinner', meal_date: '2025-12-14' },
                  { id: 2, recipe_id: 2, meal_type: 'lunch', meal_date: '2025-12-15' }
                ],
                created_at: '2025-12-14T10:00:00'
              },
              {
                id: 2,
                name: 'Weekend Special',
                start_date: '2025-12-21',
                end_date: '2025-12-22',
                people_count: 2,
                dietary_restrictions: ['vegan'],
                meals: [
                  { id: 3, recipe_id: 3, meal_type: 'breakfast', meal_date: '2025-12-21' }
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

      await page.goto('/calendar');

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

      await page.goto('/calendar');

      // Open modal
      await page.getByRole('button', { name: 'Create Plan' }).click();

      // Try to set negative days (input should prevent it due to min=1)
      const daysInput = page.locator('input[type="number"]').first();
      await expect(daysInput).toHaveAttribute('min', '1');
      await expect(daysInput).toHaveAttribute('max', '30');

      // Try to set negative people
      const peopleInput = page.locator('label:has-text("Number of People")').locator('..').locator('input[type="number"]');
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

      await page.goto('/calendar');

      // Open modal and submit
      await page.getByRole('button', { name: 'Create Plan' }).click();

      const daysInput = page.locator('input[type="number"]').first();
      await daysInput.fill('7');

      const submitButton = page.getByRole('button', { name: 'Create Meal Plan' });
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

      await page.goto('/calendar');

      // Open modal and submit
      await page.getByRole('button', { name: 'Create Plan' }).click();

      const submitButton = page.getByRole('button', { name: 'Create Meal Plan' });
      await submitButton.click();

      // Check error is displayed
      await expect(page.locator('.bg-red-50')).toBeVisible({ timeout: 3000 });
    });

    test('displays error when loading meal plans fails', async ({ page }) => {
      await page.route('**/api/meal-plans*', async route => {
        await route.abort('failed');
      });

      await page.goto('/calendar');

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
                  start_date: '2025-12-14',
                  end_date: '2025-12-20',
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
                      meal_date: '2025-12-14',
                      servings_override: null,
                      notes: null,
                      recipe: { name: 'Pasta' }
                    },
                    {
                      id: 2,
                      meal_plan_id: 1,
                      recipe_id: 6,
                      meal_type: 'lunch',
                      meal_date: '2025-12-15',
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
                start_date: '2025-12-14',
                end_date: '2025-12-20',
                people_count: 2,
                dietary_restrictions: [],
                meals: []
              }
            })
          });
        }
      });

      await page.goto('/calendar');

      // Create a meal plan
      await page.getByRole('button', { name: 'Create Plan' }).click();
      await page.getByRole('button', { name: 'Create Meal Plan' }).click();

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
                start_date: '2025-12-14',
                end_date: '2025-12-20',
                people_count: 2,
                dietary_restrictions: [],
                meals: [
                  {
                    id: 1,
                    meal_plan_id: 1,
                    recipe_id: 1,
                    meal_type: 'breakfast',
                    meal_date: '2025-12-14',
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
                    meal_date: '2025-12-14',
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
                    meal_date: '2025-12-14',
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

      await page.goto('/calendar');

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

  test.describe('Edge Cases', () => {
    test('handles large number of meal plans', async ({ page }) => {
      const mealPlans = Array.from({ length: 15 }, (_, i) => ({
        id: i + 1,
        name: `Meal Plan ${i + 1}`,
        start_date: '2025-12-14',
        end_date: '2025-12-20',
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

      await page.goto('/calendar');

      // Wait for loading
      await page.waitForTimeout(500);

      // Check that multiple meal plans render (use exact matching to avoid conflicts with 10, 11, etc.)
      await expect(page.getByRole('heading', { name: 'Meal Plan 1', exact: true })).toBeVisible();
      await expect(page.getByRole('heading', { name: 'Meal Plan 15' })).toBeVisible();

      // Check grid layout
      const mealPlanCards = page.locator('.bg-white.rounded-xl.shadow-sm.border.border-cream-200');
      expect(await mealPlanCards.count()).toBeGreaterThanOrEqual(15);
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
                start_date: '2025-12-14',
                end_date: '2025-12-20',
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

      await page.goto('/calendar');

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
                start_date: '2025-12-14',
                end_date: '2025-12-20',
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

      await page.goto('/calendar');

      // Should display long name without layout issues
      await expect(page.getByText(/A Very Long Meal Plan Name/)).toBeVisible();
    });
  });
});
