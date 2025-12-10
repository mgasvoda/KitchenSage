import { test, expect } from '@playwright/test';

/**
 * E2E tests for the Discover page covering URL parsing, AI discovery,
 * and pending recipe approval workflow.
 */

test.describe('Discover Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to discover page
    await page.goto('/discover');
    
    // Wait for page to load
    await page.waitForSelector('text=Discover Recipes');
  });

  test('renders discover page with tabs', async ({ page }) => {
    // Check that all three tabs are visible using more specific selectors
    await expect(page.getByRole('button', { name: 'Add by URL' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'AI Search' })).toBeVisible();
    await expect(page.getByRole('button', { name: /Pending Review/ })).toBeVisible();
  });

  test('URL parsing flow - parse, review, approve', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/pending-recipes/parse', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: 'Recipe parsed successfully',
            pending_recipe: {
              id: 1,
              name: 'Test Pasta Recipe',
              description: 'A delicious pasta dish',
              prep_time: 15,
              cook_time: 20,
              servings: 4,
              difficulty: 'Easy',
              cuisine: 'Italian',
              dietary_tags: ['vegetarian'],
              ingredients: [
                { name: 'pasta', quantity: 400, unit: 'g' },
                { name: 'tomato sauce', quantity: 1, unit: 'cup' },
              ],
              instructions: ['Boil pasta', 'Heat sauce', 'Combine and serve'],
              status: 'pending',
              source_url: 'https://example.com/recipe',
            },
          }),
        });
      }
    });

    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    await page.route('**/api/pending-recipes/1/approve', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          message: 'Recipe approved',
          recipe_id: 1,
        }),
      });
    });

    // Enter URL and parse
    const urlInput = page.locator('input[type="url"][placeholder*="https://example.com"]');
    await urlInput.fill('https://example.com/recipe');
    
    const parseButton = page.getByRole('button', { name: 'Parse Recipe' });
    await parseButton.click();

    // Wait for parsed recipe to appear
    await expect(page.getByText('Test Pasta Recipe')).toBeVisible({ timeout: 5000 });

    // Click approve button
    const approveButton = page.getByRole('button', { name: 'Approve' });
    await approveButton.click();

    // Wait for approval to complete
    await expect(approveButton).not.toBeVisible({ timeout: 5000 });
  });

  test('AI discovery flow - search, review, approve', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/pending-recipes/discover', async route => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: 'Found 2 recipes',
            pending_recipes: [
              {
                id: 1,
                name: 'Pasta Carbonara',
                description: 'Classic Italian pasta',
                prep_time: 10,
                cook_time: 20,
                servings: 4,
                difficulty: 'Medium',
                cuisine: 'Italian',
                dietary_tags: [],
                ingredients: [{ name: 'pasta' }, { name: 'eggs' }],
                instructions: ['Cook pasta', 'Mix eggs', 'Combine'],
                status: 'pending',
              },
              {
                id: 2,
                name: 'Spaghetti Aglio e Olio',
                description: 'Simple garlic pasta',
                prep_time: 5,
                cook_time: 15,
                servings: 2,
                difficulty: 'Easy',
                cuisine: 'Italian',
                dietary_tags: ['vegetarian'],
                ingredients: [{ name: 'spaghetti' }, { name: 'garlic' }],
                instructions: ['Cook pasta', 'Sauté garlic', 'Combine'],
                status: 'pending',
              },
            ],
            query: 'pasta recipes',
          }),
        });
      }
    });

    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    await page.route('**/api/pending-recipes/1/approve', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          recipe_id: 1,
        }),
      });
    });

    // Switch to AI Search tab
    await page.getByRole('button', { name: 'AI Search' }).click();

    // Enter search query
    const searchInput = page.locator('input[placeholder*="quick weeknight"]');
    await searchInput.fill('pasta recipes');

    // Submit search
    const searchButton = page.getByRole('button', { name: 'Discover Recipes' });
    await searchButton.click();

    // Wait for results
    await expect(page.getByText('Pasta Carbonara')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Spaghetti Aglio e Olio')).toBeVisible();

    // Approve first recipe
    const approveButtons = page.getByRole('button', { name: 'Approve' });
    await approveButtons.first().click();

    // Wait for approval
    await expect(page.getByText('Pasta Carbonara')).not.toBeVisible({ timeout: 5000 });
  });

  test('reject recipe flow', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/pending-recipes/parse', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipe: {
            id: 1,
            name: 'Test Recipe',
            status: 'pending',
            ingredients: [],
            instructions: [],
          },
        }),
      });
    });

    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    await page.route('**/api/pending-recipes/1', async route => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: 'Recipe rejected',
          }),
        });
      }
    });

    // Parse a recipe
    const urlInput = page.locator('input[type="url"][placeholder*="https://example.com"]');
    await urlInput.fill('https://example.com/recipe');
    await page.getByRole('button', { name: 'Parse Recipe' }).click();

    // Wait for recipe to appear
    await expect(page.getByText('Test Recipe')).toBeVisible({ timeout: 5000 });

    // Click reject button
    const rejectButton = page.getByRole('button', { name: 'Reject' });
    await rejectButton.click();

    // Wait for recipe to be removed
    await expect(page.getByText('Test Recipe')).not.toBeVisible({ timeout: 5000 });
  });

  test('edit before approve flow', async ({ page }) => {
    // Mock API responses
    await page.route('**/api/pending-recipes/parse', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipe: {
            id: 1,
            name: 'Original Recipe',
            description: 'Original description',
            prep_time: 10,
            cook_time: 20,
            servings: 4,
            difficulty: 'Easy',
            cuisine: 'Italian',
            ingredients: [{ name: 'flour' }, { name: 'sugar' }],
            instructions: ['Step 1', 'Step 2'],
            status: 'pending',
          },
        }),
      });
    });

    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    await page.route('**/api/pending-recipes/1', async route => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            pending_recipe: {
              id: 1,
              name: 'Edited Recipe',
              prep_time: 15,
            },
          }),
        });
      }
    });

    await page.route('**/api/pending-recipes/1/approve', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          recipe_id: 1,
        }),
      });
    });

    // Parse a recipe
    const urlInput = page.locator('input[type="url"][placeholder*="https://example.com"]');
    await urlInput.fill('https://example.com/recipe');
    await page.getByRole('button', { name: 'Parse Recipe' }).click();

    // Wait for recipe
    await expect(page.getByText('Original Recipe')).toBeVisible({ timeout: 5000 });

    // Click edit button
    const editButton = page.getByRole('button', { name: 'Edit' });
    await editButton.click();

    // Wait for edit modal
    await expect(page.getByText('Edit Recipe')).toBeVisible();

    // Edit recipe name - find input near "Name" label
    const nameLabel = page.getByText(/^Name$/i);
    const nameInput = nameLabel.locator('..').locator('input').first();
    await nameInput.clear();
    await nameInput.fill('Edited Recipe');

    // Edit prep time - find input near "Prep Time" label
    const prepTimeLabel = page.getByText(/Prep Time/i);
    const prepTimeInput = prepTimeLabel.locator('..').locator('input').first();
    await prepTimeInput.clear();
    await prepTimeInput.fill('15');

    // Save changes
    const saveButton = page.getByRole('button', { name: 'Save Changes' });
    await saveButton.click();

    // Wait for modal to close
    await expect(page.getByText('Edit Recipe')).not.toBeVisible({ timeout: 5000 });

    // Approve the edited recipe
    const approveButton = page.getByRole('button', { name: 'Approve' });
    await approveButton.click();

    // Wait for approval
    await expect(page.getByText('Edited Recipe')).not.toBeVisible({ timeout: 5000 });
  });

  test('duplicate detection', async ({ page }) => {
    // Mock list response first
    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    // Mock duplicate response (without pending_recipe when status is duplicate)
    await page.route('**/api/pending-recipes/parse', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'duplicate',
          message: 'A recipe from this URL is already pending review',
        }),
      });
    });

    // Try to parse duplicate URL
    const urlInput = page.locator('input[type="url"][placeholder*="https://example.com"]');
    await urlInput.fill('https://example.com/recipe');
    await page.getByRole('button', { name: 'Parse Recipe' }).click();

    // Check for duplicate message
    await expect(page.getByText(/already pending review/i)).toBeVisible({ timeout: 5000 });
  });

  test('pending queue navigation', async ({ page }) => {
    // Set up route BEFORE navigating to page - match exact API endpoint
    await page.route('**/api/pending-recipes', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [
            {
              id: 1,
              name: 'Pending Recipe 1',
              ingredients: [],
              instructions: [],
              status: 'pending',
            },
            {
              id: 2,
              name: 'Pending Recipe 2',
              ingredients: [],
              instructions: [],
              status: 'pending',
            },
          ],
          total: 2,
        }),
      });
    });

    // Now navigate to page (route is set up, so API call will be mocked)
    await page.goto('/discover');
    await page.waitForSelector('text=Discover Recipes');

    // Wait a moment for initial API call to complete
    await page.waitForTimeout(500);

    // Navigate to pending tab
    await page.getByRole('button', { name: /Pending Review/ }).click();

    // Wait for pending recipes to load
    await expect(page.getByText('Pending Recipe 1')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Pending Recipe 2')).toBeVisible();
  });

  test('empty pending queue', async ({ page }) => {
    // Mock empty pending list
    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    // Navigate to pending tab
    await page.getByRole('button', { name: /Pending Review/ }).click();

    // Check for empty state message
    await expect(page.getByText(/All caught up!/i)).toBeVisible({ timeout: 5000 });
  });

  test('error handling - invalid URL', async ({ page }) => {
    // Mock error response
    await page.route('**/api/pending-recipes/parse', async route => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Failed to parse URL',
        }),
      });
    });

    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    // Try to parse invalid URL
    const urlInput = page.locator('input[type="url"][placeholder*="https://example.com"]');
    await urlInput.fill('https://invalid-url.com');
    await page.getByRole('button', { name: 'Parse Recipe' }).click();

    // Check for error message
    await expect(page.getByText(/Failed to parse/i)).toBeVisible({ timeout: 5000 });
  });

  test('search with filters', async ({ page }) => {
    // Mock search response
    await page.route('**/api/pending-recipes/discover', async route => {
      const requestBody = JSON.parse(route.request().postData() || '{}');

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [
            {
              id: 1,
              name: 'Filtered Recipe',
              cuisine: requestBody.cuisine || null,
              dietary_tags: requestBody.dietary_restrictions || [],
              ingredients: [],
              instructions: [],
              status: 'pending',
            },
          ],
          query: requestBody.query,
        }),
      });
    });

    await page.route('**/api/pending-recipes/list*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [],
          total: 0,
        }),
      });
    });

    // Switch to search tab
    await page.getByRole('button', { name: 'AI Search' }).click();

    // Enter query
    const searchInput = page.locator('input[placeholder*="quick weeknight"]');
    await searchInput.fill('healthy dinner');

    // Select cuisine - find select element
    const cuisineSelect = page.locator('select').first();
    await cuisineSelect.selectOption('italian');

    // Toggle dietary restriction
    const vegetarianButton = page.getByText(/vegetarian/i);
    await vegetarianButton.click();

    // Submit search
    await page.getByRole('button', { name: 'Discover Recipes' }).click();

    // Wait for results
    await expect(page.getByText('Filtered Recipe')).toBeVisible({ timeout: 5000 });
  });

  test('recipe card interactions', async ({ page }) => {
    // Set up routes BEFORE navigating to page - match exact API endpoint
    await page.route('**/api/pending-recipes', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          pending_recipes: [
            {
              id: 1,
              name: 'Interactive Recipe',
              description: 'Test description',
              prep_time: 10,
              cook_time: 20,
              servings: 4,
              difficulty: 'Easy',
              cuisine: 'Italian',
              ingredients: [{ name: 'flour' }],
              instructions: ['Step 1'],
              status: 'pending',
            },
          ],
          total: 1,
        }),
      });
    });

    await page.route('**/api/pending-recipes/1/approve', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'success', recipe_id: 1 }),
      });
    });

    // Now navigate to page (route is set up, so API call will be mocked)
    await page.goto('/discover');
    await page.waitForSelector('text=Discover Recipes');

    // Wait a moment for initial API call to complete
    await page.waitForTimeout(500);

    // Navigate to pending tab
    await page.getByRole('button', { name: /Pending Review/ }).click();

    // Wait for recipe card
    await expect(page.getByText('Interactive Recipe')).toBeVisible({ timeout: 5000 });

    // Verify all action buttons are present
    await expect(page.getByRole('button', { name: 'Approve' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Edit' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Reject' })).toBeVisible();

    // Click approve
    await page.getByRole('button', { name: 'Approve' }).click();

    // Wait for action to complete
    await expect(page.getByText('Interactive Recipe')).not.toBeVisible({ timeout: 5000 });
  });
});

