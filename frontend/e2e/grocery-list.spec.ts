import { test, expect } from '@playwright/test';

/**
 * E2E tests for grocery list functionality covering:
 * - Single list page rendering
 * - Toggle item checked state
 * - Clear checked items
 * - Clear all items with confirmation
 * - Add ingredients from recipe
 * - Add ingredients from meal plan
 */

test.describe('Grocery List', () => {

  test.describe('Page Rendering', () => {
    test('renders grocery page with empty state', async ({ page }) => {
      // Mock empty grocery list
      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: [],
              completed: false
            }
          })
        });
      });

      await page.goto('/grocery');

      // Check main heading (use exact to avoid matching "Your grocery list is empty")
      await expect(page.getByRole('heading', { name: 'Grocery List', exact: true })).toBeVisible();

      // Check empty state message
      await expect(page.getByText('Your grocery list is empty')).toBeVisible();
      await expect(page.getByText(/Add ingredients from your recipes/)).toBeVisible();
    });

    test('renders grocery list with items grouped by category', async ({ page }) => {
      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: [
                { id: 1, ingredient_id: 1, ingredient_name: 'Tomatoes', quantity: 4, unit: 'piece', category: 'Produce', checked: false },
                { id: 2, ingredient_id: 2, ingredient_name: 'Onions', quantity: 2, unit: 'piece', category: 'Produce', checked: false },
                { id: 3, ingredient_id: 3, ingredient_name: 'Chicken Breast', quantity: 500, unit: 'g', category: 'Meat', checked: true },
                { id: 4, ingredient_id: 4, ingredient_name: 'Milk', quantity: 1, unit: 'liter', category: 'Dairy', checked: false }
              ],
              completed: false
            }
          })
        });
      });

      await page.goto('/grocery');

      // Check header shows item count
      await expect(page.getByText('1 of 4 items checked')).toBeVisible();

      // Check category groupings
      await expect(page.getByText('Produce')).toBeVisible();
      await expect(page.getByText('Meat')).toBeVisible();
      await expect(page.getByText('Dairy')).toBeVisible();

      // Check items are displayed
      await expect(page.getByText('Tomatoes')).toBeVisible();
      await expect(page.getByText('Onions')).toBeVisible();
      await expect(page.getByText('Chicken Breast')).toBeVisible();
      await expect(page.getByText('Milk')).toBeVisible();

      // Check Clear Checked button is visible (since there's 1 checked item)
      await expect(page.getByRole('button', { name: 'Clear Checked' })).toBeVisible();
      
      // Check Clear All button is visible
      await expect(page.getByRole('button', { name: 'Clear All' })).toBeVisible();
    });

    test('hides Clear Checked button when no items are checked', async ({ page }) => {
      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: [
                { id: 1, ingredient_id: 1, ingredient_name: 'Tomatoes', quantity: 4, unit: 'piece', category: 'Produce', checked: false }
              ],
              completed: false
            }
          })
        });
      });

      await page.goto('/grocery');

      // Clear Checked should NOT be visible when no items checked
      await expect(page.getByRole('button', { name: 'Clear Checked' })).not.toBeVisible();
      
      // Clear All should still be visible
      await expect(page.getByRole('button', { name: 'Clear All' })).toBeVisible();
    });
  });

  test.describe('Item Toggle', () => {
    test('toggles item checked state', async ({ page }) => {
      let itemChecked = false;

      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: [
                { id: 1, ingredient_id: 1, ingredient_name: 'Tomatoes', quantity: 4, unit: 'piece', category: 'Produce', checked: itemChecked }
              ],
              completed: false
            }
          })
        });
      });

      await page.route('**/api/grocery-lists/1/items/1*', async route => {
        if (route.request().method() === 'PUT') {
          const url = new URL(route.request().url());
          itemChecked = url.searchParams.get('checked') === 'true';
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              item_id: 1,
              checked: itemChecked
            })
          });
        }
      });

      await page.goto('/grocery');

      // Find the checkbox for Tomatoes
      const checkbox = page.locator('input[type="checkbox"]').first();
      
      // Initially unchecked
      await expect(checkbox).not.toBeChecked();

      // Click to check
      await checkbox.click();

      // Should now be checked
      await expect(checkbox).toBeChecked();

      // The text should have line-through style
      await expect(page.locator('text=Tomatoes').first()).toHaveClass(/line-through/);
    });
  });

  test.describe('Clear Actions', () => {
    test('clears checked items', async ({ page }) => {
      let cleared = false;

      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: cleared ? [
                { id: 1, ingredient_id: 1, ingredient_name: 'Tomatoes', quantity: 4, unit: 'piece', category: 'Produce', checked: false }
              ] : [
                { id: 1, ingredient_id: 1, ingredient_name: 'Tomatoes', quantity: 4, unit: 'piece', category: 'Produce', checked: false },
                { id: 2, ingredient_id: 2, ingredient_name: 'Chicken Breast', quantity: 500, unit: 'g', category: 'Meat', checked: true }
              ],
              completed: false
            }
          })
        });
      });

      await page.route('**/api/grocery-lists/1/checked', async route => {
        if (route.request().method() === 'DELETE') {
          cleared = true;
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              deleted_count: 1
            })
          });
        }
      });

      await page.goto('/grocery');

      // Verify both items are visible
      await expect(page.getByText('Tomatoes')).toBeVisible();
      await expect(page.getByText('Chicken Breast')).toBeVisible();

      // Click Clear Checked
      await page.getByRole('button', { name: 'Clear Checked' }).click();

      // Wait for reload - checked item should be gone
      await expect(page.getByText('Chicken Breast')).not.toBeVisible({ timeout: 5000 });
      
      // Unchecked item should still be visible
      await expect(page.getByText('Tomatoes')).toBeVisible();
    });

    test('clears all items with confirmation', async ({ page }) => {
      let cleared = false;

      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: cleared ? [] : [
                { id: 1, ingredient_id: 1, ingredient_name: 'Tomatoes', quantity: 4, unit: 'piece', category: 'Produce', checked: false },
                { id: 2, ingredient_id: 2, ingredient_name: 'Onions', quantity: 2, unit: 'piece', category: 'Produce', checked: false }
              ],
              completed: false
            }
          })
        });
      });

      await page.route('**/api/grocery-lists/1/items', async route => {
        if (route.request().method() === 'DELETE') {
          cleared = true;
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              deleted_count: 2
            })
          });
        }
      });

      await page.goto('/grocery');

      // Verify items are visible
      await expect(page.getByText('Tomatoes')).toBeVisible();
      await expect(page.getByText('Onions')).toBeVisible();

      // Click Clear All
      await page.getByRole('button', { name: 'Clear All' }).click();

      // Confirmation modal should appear
      await expect(page.getByText('Clear All Items?')).toBeVisible();
      await expect(page.getByText('This will remove all 2 items')).toBeVisible();

      // Click Cancel - modal should close, items still there
      await page.getByRole('button', { name: 'Cancel' }).click();
      await expect(page.getByText('Clear All Items?')).not.toBeVisible();
      await expect(page.getByText('Tomatoes')).toBeVisible();

      // Click Clear All again and confirm
      await page.getByRole('button', { name: 'Clear All' }).click();
      await page.locator('.fixed').getByRole('button', { name: 'Clear All' }).click();

      // Items should be gone, empty state shown
      await expect(page.getByText('Your grocery list is empty')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Add from Recipe', () => {
    test('adds ingredients from recipe to grocery list', async ({ page }) => {
      // Mock recipes list
      await page.route('**/api/recipes*', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              recipes: [
                {
                  id: 1,
                  name: 'Pasta Carbonara',
                  description: 'Classic Italian pasta',
                  prep_time: 10,
                  cook_time: 20,
                  servings: 4,
                  difficulty: 'medium',
                  cuisine: 'italian',
                  dietary_tags: [],
                  ingredients: [
                    { ingredient: { name: 'Pasta' }, quantity: 400, unit: 'g' },
                    { ingredient: { name: 'Eggs' }, quantity: 4, unit: 'piece' },
                    { ingredient: { name: 'Bacon' }, quantity: 200, unit: 'g' }
                  ],
                  instructions: ['Boil pasta', 'Cook bacon', 'Mix eggs', 'Combine']
                }
              ],
              total: 1,
              limit: 50,
              offset: 0
            })
          });
        }
      });

      // Mock add from recipe
      await page.route('**/api/grocery-lists/add-from-recipe*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: "Added 3 ingredients from 'Pasta Carbonara' to grocery list",
            grocery_list: {
              id: 1,
              items: [
                { id: 1, ingredient_name: 'Pasta', quantity: 400, unit: 'g', category: 'Grains', checked: false },
                { id: 2, ingredient_name: 'Eggs', quantity: 4, unit: 'piece', category: 'Dairy', checked: false },
                { id: 3, ingredient_name: 'Bacon', quantity: 200, unit: 'g', category: 'Meat', checked: false }
              ]
            }
          })
        });
      });

      await page.goto('/recipes');

      // Wait for recipes to load
      await expect(page.getByText('Pasta Carbonara')).toBeVisible();

      // Click on recipe to open detail modal
      await page.locator('.cursor-pointer').filter({ hasText: 'Pasta Carbonara' }).first().click();

      // Modal should open - look for the h2 in the modal specifically
      await expect(page.locator('.fixed h2').filter({ hasText: 'Pasta Carbonara' })).toBeVisible({ timeout: 5000 });

      // Check ingredients are shown in the modal - look in ingredient list items specifically
      // The ingredients section contains list items with the ingredient names
      await expect(page.locator('.fixed li').filter({ hasText: '400 g Pasta' })).toBeVisible();
      await expect(page.locator('.fixed li').filter({ hasText: '4 piece Eggs' })).toBeVisible();

      // Click Add to Grocery List button in the modal
      await page.locator('.fixed').getByRole('button', { name: 'Add to Grocery List' }).click();

      // Wait for success message in the modal
      await expect(page.locator('.fixed').getByText(/Added 3 ingredients/)).toBeVisible({ timeout: 5000 });
    });

    test('shows error when add from recipe fails', async ({ page }) => {
      await page.route('**/api/recipes*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            recipes: [
              {
                id: 1,
                name: 'Test Recipe',
                prep_time: 10,
                cook_time: 20,
                servings: 4,
                difficulty: 'easy',
                cuisine: 'italian',
                ingredients: [],
                instructions: []
              }
            ],
            total: 1
          })
        });
      });

      await page.route('**/api/grocery-lists/add-from-recipe*', async route => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Recipe has no ingredients'
          })
        });
      });

      await page.goto('/recipes');

      await page.getByText('Test Recipe').click();
      await page.getByRole('button', { name: 'Add to Grocery List' }).click();

      // Error message should appear
      await expect(page.getByText(/Recipe has no ingredients|Failed/)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Add from Meal Plan', () => {
    test('adds ingredients from meal plan to grocery list', async ({ page }) => {
      // Mock meal plans list
      await page.route('**/api/meal-plans*', async route => {
        if (route.request().method() === 'GET' && !route.request().url().includes('/1')) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plans: [
                {
                  id: 1,
                  name: 'Weekly Meal Plan',
                  start_date: '2025-12-14',
                  end_date: '2025-12-20',
                  people_count: 2,
                  dietary_restrictions: [],
                  meals: [
                    {
                      id: 1,
                      recipe_id: 1,
                      meal_type: 'dinner',
                      meal_date: '2025-12-14',
                      recipe: { name: 'Pasta Carbonara' }
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

      // Mock meal plan detail
      await page.route('**/api/meal-plans/1', async route => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'success',
              meal_plan: {
                id: 1,
                name: 'Weekly Meal Plan',
                start_date: '2025-12-14',
                end_date: '2025-12-20',
                people_count: 2,
                dietary_restrictions: [],
                meals: [
                  {
                    id: 1,
                    recipe_id: 1,
                    meal_type: 'dinner',
                    meal_date: '2025-12-14',
                    recipe: {
                      name: 'Pasta Carbonara',
                      description: 'Classic Italian pasta',
                      prep_time: 10,
                      cook_time: 20,
                      difficulty: 'medium',
                      cuisine: 'italian',
                      dietary_tags: []
                    }
                  }
                ]
              }
            })
          });
        }
      });

      // Mock add from meal plan
      await page.route('**/api/grocery-lists/add-from-meal-plan*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: "Added 5 ingredients from meal plan 'Weekly Meal Plan' to grocery list",
            grocery_list: {
              id: 1,
              items: []
            }
          })
        });
      });

      await page.goto('/calendar');

      // Wait for meal plans to load
      await expect(page.getByText('Weekly Meal Plan')).toBeVisible();

      // Click on meal plan to open detail modal (click the card, not just the text)
      await page.locator('.cursor-pointer').filter({ hasText: 'Weekly Meal Plan' }).first().click();

      // Wait for modal to load - look for the h2 in the modal specifically
      await expect(page.locator('.fixed h2').filter({ hasText: 'Weekly Meal Plan' })).toBeVisible({ timeout: 5000 });

      // Click Add to Grocery List button in the modal
      await page.locator('.fixed').getByRole('button', { name: 'Add to Grocery List' }).click();

      // Wait for success message
      await expect(page.getByText(/Added 5 ingredients/)).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Error Handling', () => {
    test('displays error when loading grocery list fails', async ({ page }) => {
      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Database error'
          })
        });
      });

      await page.goto('/grocery');

      // Error should be displayed
      await expect(page.locator('.bg-red-50')).toBeVisible({ timeout: 3000 });
    });

    test('handles network errors gracefully', async ({ page }) => {
      await page.route('**/api/grocery-lists/default', async route => {
        await route.abort('failed');
      });

      await page.goto('/grocery');

      // Error should be displayed
      await expect(page.locator('.bg-red-50')).toBeVisible({ timeout: 3000 });
    });
  });

  test.describe('Edge Cases', () => {
    test('handles grocery list with many items', async ({ page }) => {
      const items = Array.from({ length: 25 }, (_, i) => ({
        id: i + 1,
        ingredient_id: i + 1,
        ingredient_name: `Item ${i + 1}`,
        quantity: i + 1,
        unit: 'piece',
        category: i % 3 === 0 ? 'Produce' : (i % 3 === 1 ? 'Meat' : 'Dairy'),
        checked: i % 5 === 0
      }));

      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: items,
              completed: false
            }
          })
        });
      });

      await page.goto('/grocery');

      // Should display all categories
      await expect(page.getByText('Produce')).toBeVisible();
      await expect(page.getByText('Meat')).toBeVisible();
      await expect(page.getByText('Dairy')).toBeVisible();

      // Should show correct item count (5 items checked out of 25)
      await expect(page.getByText('5 of 25 items checked')).toBeVisible();
    });

    test('handles items with long names', async ({ page }) => {
      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: [
                {
                  id: 1,
                  ingredient_id: 1,
                  ingredient_name: 'Extra Virgin Cold Pressed Organic Olive Oil from Italy',
                  quantity: 500,
                  unit: 'ml',
                  category: 'Pantry',
                  checked: false
                }
              ],
              completed: false
            }
          })
        });
      });

      await page.goto('/grocery');

      // Should display long name without layout issues
      await expect(page.getByText(/Extra Virgin Cold Pressed/)).toBeVisible();
    });

    test('handles unknown category', async ({ page }) => {
      await page.route('**/api/grocery-lists/default', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            grocery_list: {
              id: 1,
              meal_plan_id: null,
              items: [
                { id: 1, ingredient_id: 1, ingredient_name: 'Mystery Item', quantity: 1, unit: 'piece', category: 'Unknown Category', checked: false }
              ],
              completed: false
            }
          })
        });
      });

      await page.goto('/grocery');

      // Should display with fallback icon (Other category)
      await expect(page.getByText('Unknown Category')).toBeVisible();
      await expect(page.getByText('Mystery Item')).toBeVisible();
    });
  });
});
