import { test, expect } from '@playwright/test';

/**
 * E2E tests for async grocery list generation from meal plans
 * Tests the new toast notification workflow with background processing
 */

test.describe('Async Grocery List from Meal Plan', () => {

  test('adds meal plan to grocery list with toast notification', async ({ page }) => {
    let taskId = 'test-task-123';
    let taskStatus = 'pending';
    let taskResult = null;

    // Mock meal plans list
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
                name: 'Weekly Plan',
                is_active: true,
                people_count: 2,
                dietary_restrictions: [],
                meals: [
                  {
                    id: 1,
                    recipe_id: 1,
                    meal_type: 'dinner',
                    day_number: 1,
                    recipe: {
                      id: 1,
                      name: 'Pasta Primavera',
                      servings: 2
                    }
                  },
                  {
                    id: 2,
                    recipe_id: 2,
                    meal_type: 'lunch',
                    day_number: 2,
                    recipe: {
                      id: 2,
                      name: 'Caesar Salad',
                      servings: 2
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
      }
    });

    // Mock meal plan detail endpoint
    await page.route('**/api/meal-plans/1', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          meal_plan: {
            id: 1,
            name: 'Weekly Plan',
            is_active: true,
            people_count: 2,
            dietary_restrictions: [],
            meals: [
              {
                id: 1,
                recipe_id: 1,
                meal_type: 'dinner',
                day_number: 1,
                servings_override: null,
                notes: null,
                recipe: {
                  id: 1,
                  name: 'Pasta Primavera',
                  servings: 2,
                  description: 'Fresh vegetable pasta',
                  prep_time: 15,
                  cook_time: 20,
                  difficulty: 'easy',
                  cuisine: 'italian',
                  dietary_tags: ['vegetarian']
                }
              },
              {
                id: 2,
                recipe_id: 2,
                meal_type: 'lunch',
                day_number: 2,
                servings_override: null,
                notes: null,
                recipe: {
                  id: 2,
                  name: 'Caesar Salad',
                  servings: 2,
                  description: 'Classic Caesar salad',
                  prep_time: 10,
                  cook_time: 0,
                  difficulty: 'easy',
                  cuisine: 'italian',
                  dietary_tags: []
                }
              }
            ],
            created_at: '2025-12-14T10:00:00'
          }
        })
      });
    });

    // Mock async add-from-meal-plan endpoint (returns task_id immediately)
    await page.route('**/api/grocery-lists/add-from-meal-plan*', async route => {
      taskStatus = 'processing';
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          task_id: taskId,
          message: 'Task started. Poll /tasks/{task_id} for status.'
        })
      });
    });

    // Mock task status endpoint (simulates async processing)
    let pollCount = 0;
    await page.route('**/api/grocery-lists/tasks/*', async route => {
      pollCount++;

      // Simulate processing for first 2 polls, then complete
      if (pollCount <= 2) {
        taskStatus = 'processing';
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            task: {
              id: taskId,
              status: 'processing',
              created_at: '2025-12-14T10:00:00',
              updated_at: '2025-12-14T10:00:05',
              result: null,
              error: null,
              metadata: {
                operation: 'add_meal_plan_ingredients',
                meal_plan_id: 1
              }
            }
          })
        });
      } else {
        // After 2 polls, mark as completed
        taskStatus = 'completed';
        taskResult = {
          status: 'success',
          message: 'Added 12 ingredients from \'Weekly Plan\' to grocery list',
          grocery_list: {
            id: 1,
            name: 'My Grocery List',
            items: []
          }
        };
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            task: {
              id: taskId,
              status: 'completed',
              created_at: '2025-12-14T10:00:00',
              updated_at: '2025-12-14T10:00:10',
              result: taskResult,
              error: null,
              metadata: {
                operation: 'add_meal_plan_ingredients',
                meal_plan_id: 1
              }
            }
          })
        });
      }
    });

    await page.goto('/meal-plans');
    
    // Wait for meal plan card to render
    await page.waitForSelector('h3:text("Weekly Plan")', { state: 'visible', timeout: 10000 });
    
    // Click on the entire card (the h3's parent div has onClick)
    const weeklyPlanCard = page.locator('div.bg-white').filter({ has: page.locator('h3:text("Weekly Plan")') });
    await weeklyPlanCard.click();

    // Wait for modal to open (check for the h2 meal plan name in header - h3 is on the card)
    await expect(page.getByRole('heading', { name: 'Weekly Plan', level: 2 })).toBeVisible({ timeout: 3000 });

    // Verify meals are displayed in modal (use heading role to avoid matching descriptions)
    await expect(page.getByRole('heading', { name: 'Pasta Primavera' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Caesar Salad' })).toBeVisible();

    // Click "Add to Grocery List" button
    await page.getByRole('button', { name: 'Add to Grocery List' }).click();

    // Modal should close immediately
    await expect(page.getByText('Meal Plan Details')).not.toBeVisible({ timeout: 2000 });

    // Toast notification should appear with "processing" message
    await expect(page.getByText('Adding ingredients to grocery list...')).toBeVisible({ timeout: 2000 });

    // Wait for success toast (mock polling completes quickly)
    // Use a longer timeout to allow for polling, but check for the toast update
    await expect(page.getByText(/Added 12 ingredients/)).toBeVisible({ timeout: 10000 });

    // Success toast should have "View Grocery List" action link (styled as button)
    // Check immediately before auto-dismiss (5s timer)
    await expect(page.getByText('View Grocery List')).toBeVisible({ timeout: 2000 });
  });

  test('handles async grocery list error with retry', async ({ page }) => {
    let taskId = 'test-task-error-456';
    let attemptCount = 0;

    // Mock meal plans
    await page.route('**/api/meal-plans*', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            meal_plans: [
              {
                id: 2,
                name: 'Error Plan',
                is_active: false,
                people_count: 2,
                dietary_restrictions: [],
                meals: [{ id: 3, recipe_id: 3, meal_type: 'dinner', day_number: 1, recipe: { name: 'Test Recipe' } }],
                created_at: '2025-12-14T10:00:00'
              }
            ],
            total: 1,
            limit: 50,
            offset: 0
          })
        });
      }
    });

    // Mock meal plan detail
    await page.route('**/api/meal-plans/2', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          meal_plan: {
            id: 2,
            name: 'Error Plan',
            is_active: false,
            people_count: 2,
            dietary_restrictions: [],
            meals: [{
              id: 3,
              recipe_id: 3,
              meal_type: 'dinner',
              day_number: 1,
              recipe: { id: 3, name: 'Test Recipe', servings: 2 }
            }],
            created_at: '2025-12-14T10:00:00'
          }
        })
      });
    });

    // Mock async endpoint
    await page.route('**/api/grocery-lists/add-from-meal-plan*', async route => {
      attemptCount++;
      taskId = `test-task-error-${attemptCount}`;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          task_id: taskId,
          message: 'Task started.'
        })
      });
    });

    // Mock task status - first attempt fails, second succeeds
    await page.route('**/api/grocery-lists/tasks/*', async route => {
      if (attemptCount === 1) {
        // First attempt - return failed status
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            task: {
              id: taskId,
              status: 'failed',
              created_at: '2025-12-14T10:00:00',
              updated_at: '2025-12-14T10:00:05',
              result: null,
              error: 'LLM consolidation service unavailable',
              metadata: { operation: 'add_meal_plan_ingredients', meal_plan_id: 2 }
            }
          })
        });
      } else {
        // Second attempt (after retry) - return success
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            task: {
              id: taskId,
              status: 'completed',
              created_at: '2025-12-14T10:00:00',
              updated_at: '2025-12-14T10:00:10',
              result: {
                status: 'success',
                message: 'Added 5 ingredients from \'Error Plan\' to grocery list'
              },
              error: null,
              metadata: { operation: 'add_meal_plan_ingredients', meal_plan_id: 2 }
            }
          })
        });
      }
    });

    await page.goto('/meal-plans');
    
    // Wait for meal plan card to render
    await page.waitForSelector('h3:text("Error Plan")', { state: 'visible', timeout: 10000 });

    // Click meal plan card
    const errorPlanCard = page.locator('div.bg-white').filter({ has: page.locator('h3:text("Error Plan")') });
    await errorPlanCard.click();
    await expect(page.getByText('Test Recipe')).toBeVisible({ timeout: 3000 });

    // Click add to grocery list
    await page.getByRole('button', { name: 'Add to Grocery List' }).click();

    // Modal closes
    await page.waitForTimeout(500);

    // Wait for error toast
    await page.waitForTimeout(3000);
    await expect(page.getByText(/LLM consolidation service unavailable/)).toBeVisible({ timeout: 3000 });

    // Error toast should have Retry button
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();

    // Click retry
    await page.getByRole('button', { name: 'Retry' }).click();

    // Wait for success after retry
    await page.waitForTimeout(4000);
    await expect(page.getByText(/Added 5 ingredients/)).toBeVisible({ timeout: 3000 });
  });

  test('dismisses toast notification manually', async ({ page }) => {
    // Mock meal plans
    await page.route('**/api/meal-plans*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          meal_plans: [
            {
              id: 3,
              name: 'Dismiss Test Plan',
              is_active: false,
              people_count: 2,
              dietary_restrictions: [],
              meals: [{ id: 4, recipe_id: 4, meal_type: 'breakfast', day_number: 1, recipe: { name: 'Omelette' } }],
              created_at: '2025-12-14T10:00:00'
            }
          ],
          total: 1,
          limit: 50,
          offset: 0
        })
      });
    });

    await page.route('**/api/meal-plans/3', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          meal_plan: {
            id: 3,
            name: 'Dismiss Test Plan',
            is_active: false,
            people_count: 2,
            dietary_restrictions: [],
            meals: [{
              id: 4,
              recipe_id: 4,
              meal_type: 'breakfast',
              day_number: 1,
              recipe: { id: 4, name: 'Omelette', servings: 2 }
            }],
            created_at: '2025-12-14T10:00:00'
          }
        })
      });
    });

    await page.route('**/api/grocery-lists/add-from-meal-plan*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          task_id: 'test-dismiss-789',
          message: 'Task started.'
        })
      });
    });

    await page.route('**/api/grocery-lists/tasks/*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          task: {
            id: 'test-dismiss-789',
            status: 'completed',
            created_at: '2025-12-14T10:00:00',
            updated_at: '2025-12-14T10:00:05',
            result: {
              status: 'success',
              message: 'Added 3 ingredients to grocery list'
            },
            error: null,
            metadata: { operation: 'add_meal_plan_ingredients', meal_plan_id: 3 }
          }
        })
      });
    });

    await page.goto('/meal-plans');
    
    // Wait for meal plan card to render
    await page.waitForSelector('h3:text("Dismiss Test Plan")', { state: 'visible', timeout: 10000 });

    const dismissPlanCard = page.locator('div.bg-white').filter({ has: page.locator('h3:text("Dismiss Test Plan")') });
    await dismissPlanCard.click();
    await page.getByRole('button', { name: 'Add to Grocery List' }).click();

    // Wait for success toast
    await page.waitForTimeout(3000);
    await expect(page.getByText(/Added 3 ingredients/)).toBeVisible();

    // Click dismiss button (X icon)
    const dismissButton = page.locator('[aria-label="Dismiss"]').first();
    await dismissButton.click();

    // Toast should disappear
    await expect(page.getByText(/Added 3 ingredients/)).not.toBeVisible({ timeout: 1000 });
  });

  test('navigates to grocery page when clicking View Grocery List', async ({ page }) => {
    // Mock all necessary endpoints
    await page.route('**/api/meal-plans*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          meal_plans: [
            {
              id: 4,
              name: 'Navigation Test Plan',
              is_active: false,
              people_count: 2,
              dietary_restrictions: [],
              meals: [{ id: 5, recipe_id: 5, meal_type: 'lunch', day_number: 1, recipe: { name: 'Sandwich' } }],
              created_at: '2025-12-14T10:00:00'
            }
          ],
          total: 1,
          limit: 50,
          offset: 0
        })
      });
    });

    await page.route('**/api/meal-plans/4', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          meal_plan: {
            id: 4,
            name: 'Navigation Test Plan',
            is_active: false,
            people_count: 2,
            dietary_restrictions: [],
            meals: [{
              id: 5,
              recipe_id: 5,
              meal_type: 'lunch',
              day_number: 1,
              recipe: { id: 5, name: 'Sandwich', servings: 2 }
            }],
            created_at: '2025-12-14T10:00:00'
          }
        })
      });
    });

    await page.route('**/api/grocery-lists/add-from-meal-plan*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          task_id: 'test-nav-999',
          message: 'Task started.'
        })
      });
    });

    await page.route('**/api/grocery-lists/tasks/*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          task: {
            id: 'test-nav-999',
            status: 'completed',
            result: {
              status: 'success',
              message: 'Added 2 ingredients to grocery list'
            },
            error: null
          }
        })
      });
    });

    // Mock grocery list endpoint for navigation
    await page.route('**/api/grocery-lists/default', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          grocery_list: {
            id: 1,
            name: 'My Grocery List',
            items: []
          }
        })
      });
    });

    await page.goto('/meal-plans');
    
    // Wait for meal plan card to render
    await page.waitForSelector('h3:text("Navigation Test Plan")', { state: 'visible', timeout: 10000 });

    const navPlanCard = page.locator('div.bg-white').filter({ has: page.locator('h3:text("Navigation Test Plan")') });
    await navPlanCard.click();
    await page.getByRole('button', { name: 'Add to Grocery List' }).click();

    // Wait for success toast
    await page.waitForTimeout(3000);
    await expect(page.getByText(/Added 2 ingredients/)).toBeVisible();

    // Click "View Grocery List" button
    await page.getByRole('button', { name: 'View Grocery List' }).click();

    // Should navigate to grocery page
    await expect(page).toHaveURL('/grocery', { timeout: 3000 });
    
    // Grocery page heading should be visible (h1 specifically)
    await expect(page.getByRole('heading', { name: 'Grocery List', level: 1 })).toBeVisible();
  });
});
