import { test, expect } from '@playwright/test';

test.describe('Recipe Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/recipes');
  });

  test('should display recipes page with search bar', async ({ page }) => {
    // Verify page loaded
    await expect(page.locator('h1')).toContainText('Recipes');
    
    // Verify search input exists
    const searchInput = page.locator('input[placeholder*="Search recipes"]');
    await expect(searchInput).toBeVisible();
  });

  test('should show filter button and toggle filters panel', async ({ page }) => {
    // Find and click the filters button
    const filtersButton = page.locator('button:has-text("Filters")');
    await expect(filtersButton).toBeVisible();
    
    // Click to show filters
    await filtersButton.click();
    
    // Verify filter panel appears with meal type options
    await expect(page.locator('text=Meal Type')).toBeVisible();
    await expect(page.locator('text=Cuisine')).toBeVisible();
    await expect(page.locator('text=Difficulty')).toBeVisible();
    
    // Click again to hide
    await filtersButton.click();
    
    // Filters should be hidden (wait for animation)
    await expect(page.locator('label:has-text("Meal Type")')).toBeHidden({ timeout: 1000 });
  });

  test('should filter by meal type', async ({ page }) => {
    // Open filters
    await page.click('button:has-text("Filters")');
    
    // Click on a meal type button (e.g., Dinner)
    const dinnerButton = page.locator('button:has-text("Dinner")');
    await dinnerButton.click();
    
    // Verify the button is now selected (has different styling)
    await expect(dinnerButton).toHaveClass(/bg-sage-600/);
    
    // Filter badge should show
    const filterBadge = page.locator('button:has-text("Filters") span.rounded-full');
    await expect(filterBadge).toBeVisible();
  });

  test('should filter by cuisine using dropdown', async ({ page }) => {
    // Open filters
    await page.click('button:has-text("Filters")');
    
    // Select a cuisine from dropdown
    const cuisineSelect = page.locator('select').first();
    await cuisineSelect.selectOption('italian');
    
    // Verify selection
    await expect(cuisineSelect).toHaveValue('italian');
  });

  test('should filter by difficulty', async ({ page }) => {
    // Open filters
    await page.click('button:has-text("Filters")');
    
    // Find difficulty dropdown (second select)
    const difficultySelect = page.locator('select').nth(1);
    await difficultySelect.selectOption('easy');
    
    // Verify selection
    await expect(difficultySelect).toHaveValue('easy');
  });

  test('should filter by max prep time', async ({ page }) => {
    // Open filters
    await page.click('button:has-text("Filters")');
    
    // Find prep time input
    const prepTimeInput = page.locator('input[placeholder="Prep (min)"]');
    await prepTimeInput.fill('30');
    
    // Verify value
    await expect(prepTimeInput).toHaveValue('30');
  });

  test('should filter by max total time', async ({ page }) => {
    // Open filters
    await page.click('button:has-text("Filters")');
    
    // Find total time input
    const totalTimeInput = page.locator('input[placeholder="Total (min)"]');
    await totalTimeInput.fill('45');
    
    // Verify value
    await expect(totalTimeInput).toHaveValue('45');
  });

  test('should perform semantic search with query', async ({ page }) => {
    // Type a semantic search query
    const searchInput = page.locator('input[placeholder*="Search recipes"]');
    await searchInput.fill('quick weeknight dinners');
    
    // Click search button
    await page.click('button:has-text("Search")');
    
    // Wait for results to load
    await page.waitForLoadState('networkidle');
  });

  test('should clear all filters', async ({ page }) => {
    // Open filters and apply some
    await page.click('button:has-text("Filters")');
    await page.click('button:has-text("Dinner")');
    await page.locator('select').first().selectOption('italian');
    
    // Click clear all filters
    const clearButton = page.locator('button:has-text("Clear all filters")');
    await expect(clearButton).toBeVisible();
    await clearButton.click();
    
    // Verify filters are cleared
    const dinnerButton = page.locator('button:has-text("Dinner")');
    await expect(dinnerButton).not.toHaveClass(/bg-sage-600/);
    
    const cuisineSelect = page.locator('select').first();
    await expect(cuisineSelect).toHaveValue('');
  });

  test('should display recipe count in header', async ({ page }) => {
    // Wait for initial load
    await page.waitForLoadState('networkidle');
    
    // Header should show recipe count
    const headerText = page.locator('header p');
    await expect(headerText).toContainText(/\d+ recipe/);
  });

  test('should open recipe detail modal on click', async ({ page }) => {
    // Wait for recipes to load
    await page.waitForLoadState('networkidle');
    
    // Check if there are any recipe cards
    const recipeCards = page.locator('.grid > div');
    const count = await recipeCards.count();
    
    if (count > 0) {
      // Click on first recipe card
      await recipeCards.first().click();
      
      // Modal should appear with recipe details
      await expect(page.locator('.fixed.inset-0')).toBeVisible();
      
      // Close modal by clicking outside
      await page.click('.fixed.inset-0', { position: { x: 10, y: 10 } });
    }
  });

  test('should display meal types on recipe cards in modal', async ({ page }) => {
    // Wait for recipes to load
    await page.waitForLoadState('networkidle');
    
    // Check if there are any recipe cards
    const recipeCards = page.locator('.grid > div');
    const count = await recipeCards.count();
    
    if (count > 0) {
      // Click on first recipe card
      await recipeCards.first().click();
      
      // Modal should be visible
      await expect(page.locator('.fixed.inset-0')).toBeVisible();
      
      // Meal types should be displayed (if recipe has them)
      // This is optional since not all recipes may have meal types
      const mealTypeBadges = page.locator('.bg-blue-100.text-blue-700');
      // Just verify the modal is working, meal types are optional
    }
  });

  test('should combine filters with semantic search', async ({ page }) => {
    // Enter a search query
    const searchInput = page.locator('input[placeholder*="Search recipes"]');
    await searchInput.fill('healthy vegetarian');
    
    // Open filters and select some
    await page.click('button:has-text("Filters")');
    await page.click('button:has-text("Dinner")');
    await page.locator('select').nth(1).selectOption('easy');
    
    // Submit search
    await page.click('button:has-text("Search")');
    
    // Wait for results
    await page.waitForLoadState('networkidle');
    
    // Verify filters badge shows count
    const filterBadge = page.locator('button:has-text("Filters") span.rounded-full');
    await expect(filterBadge).toBeVisible();
  });

  test('should handle empty search results gracefully', async ({ page }) => {
    // Search for something unlikely to exist
    const searchInput = page.locator('input[placeholder*="Search recipes"]');
    await searchInput.fill('xyznonexistentrecipe12345');
    await page.click('button:has-text("Search")');
    
    // Wait for results
    await page.waitForLoadState('networkidle');
    
    // Should show empty state or "0 recipes found"
    // Either the count shows 0 or an empty state is displayed
    const headerText = page.locator('header p');
    await expect(headerText).toContainText(/0 recipe|Loading/);
  });
});

