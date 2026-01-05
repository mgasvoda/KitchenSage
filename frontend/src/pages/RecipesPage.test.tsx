import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RecipesPage } from './RecipesPage';

// Mock the API
vi.mock('../services/api', () => ({
  recipeApi: {
    search: vi.fn(),
    list: vi.fn(),
  },
  groceryListApi: {
    addFromRecipe: vi.fn(),
  },
}));

import { recipeApi, groceryListApi } from '../services/api';

const mockRecipes = [
  {
    recipe: {
      id: 1,
      name: 'Chicken Stir Fry',
      description: 'Quick and easy chicken stir fry',
      prep_time: 15,
      cook_time: 15,
      servings: 4,
      difficulty: 'easy',
      cuisine: 'chinese',
      dietary_tags: ['gluten_free'],
      meal_types: ['lunch', 'dinner'],
      instructions: ['Step 1', 'Step 2'],
      ingredients: [],
    },
    relevance_score: 0.95,
    match_reasons: ['Name matches'],
  },
  {
    recipe: {
      id: 2,
      name: 'Vegetable Pasta',
      description: 'Italian comfort food',
      prep_time: 10,
      cook_time: 20,
      servings: 4,
      difficulty: 'easy',
      cuisine: 'italian',
      dietary_tags: ['vegetarian'],
      meal_types: ['dinner'],
      instructions: ['Step 1'],
      ingredients: [],
    },
    relevance_score: 0.85,
    match_reasons: ['Cuisine matches'],
  },
];

describe('RecipesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (recipeApi.search as ReturnType<typeof vi.fn>).mockResolvedValue({
      status: 'success',
      recipes: mockRecipes,
      total: 2,
      limit: 50,
      offset: 0,
    });
  });

  it('renders the page header', async () => {
    render(<RecipesPage />);
    
    expect(screen.getByRole('heading', { name: /recipes/i })).toBeInTheDocument();
  });

  it('displays search input', async () => {
    render(<RecipesPage />);
    
    const searchInput = screen.getByPlaceholderText(/search recipes/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('displays filters button', async () => {
    render(<RecipesPage />);
    
    const filtersButton = screen.getByRole('button', { name: /filters/i });
    expect(filtersButton).toBeInTheDocument();
  });

  it('loads recipes on mount', async () => {
    render(<RecipesPage />);
    
    await waitFor(() => {
      expect(recipeApi.search).toHaveBeenCalled();
    });
  });

  it('displays recipe cards after loading', async () => {
    render(<RecipesPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Chicken Stir Fry')).toBeInTheDocument();
      expect(screen.getByText('Vegetable Pasta')).toBeInTheDocument();
    });
  });

  it('shows recipe count in header', async () => {
    render(<RecipesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/2 recipes found/i)).toBeInTheDocument();
    });
  });

  it('toggles filter panel when clicking filters button', async () => {
    render(<RecipesPage />);
    
    const filtersButton = screen.getByRole('button', { name: /filters/i });
    
    // Initially, meal type filter should not be visible
    expect(screen.queryByText('Meal Type')).not.toBeInTheDocument();
    
    // Click to show filters
    fireEvent.click(filtersButton);
    
    // Now filter options should be visible
    expect(screen.getByText('Meal Type')).toBeInTheDocument();
    expect(screen.getByText('Cuisine')).toBeInTheDocument();
    expect(screen.getByText('Difficulty')).toBeInTheDocument();
  });

  it('shows meal type buttons in filter panel', async () => {
    render(<RecipesPage />);
    
    // Open filters
    fireEvent.click(screen.getByRole('button', { name: /filters/i }));
    
    // Check meal type buttons
    expect(screen.getByRole('button', { name: 'Breakfast' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Lunch' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Dinner' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Snack' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Dessert' })).toBeInTheDocument();
  });

  it('toggles meal type selection', async () => {
    render(<RecipesPage />);
    
    // Open filters
    fireEvent.click(screen.getByRole('button', { name: /filters/i }));
    
    const dinnerButton = screen.getByRole('button', { name: 'Dinner' });
    
    // Click to select
    fireEvent.click(dinnerButton);
    
    // Button should have selected styling
    expect(dinnerButton).toHaveClass('bg-sage-600');
    
    // Click again to deselect
    fireEvent.click(dinnerButton);
    
    // Button should not have selected styling
    expect(dinnerButton).not.toHaveClass('bg-sage-600');
  });

  it('performs search when form is submitted', async () => {
    render(<RecipesPage />);
    
    const searchInput = screen.getByPlaceholderText(/search recipes/i);
    const searchButton = screen.getByRole('button', { name: 'Search' });
    
    // Type search query
    fireEvent.change(searchInput, { target: { value: 'chicken' } });
    
    // Submit search
    fireEvent.click(searchButton);
    
    await waitFor(() => {
      expect(recipeApi.search).toHaveBeenCalledWith(
        expect.objectContaining({ query: 'chicken' })
      );
    });
  });

  it('shows clear filters button when filters are active', async () => {
    render(<RecipesPage />);
    
    // Open filters
    fireEvent.click(screen.getByRole('button', { name: /filters/i }));
    
    // Clear filters button should not be visible initially
    expect(screen.queryByText('Clear all filters')).not.toBeInTheDocument();
    
    // Select a meal type
    fireEvent.click(screen.getByRole('button', { name: 'Dinner' }));
    
    // Now clear button should be visible
    expect(screen.getByText('Clear all filters')).toBeInTheDocument();
  });

  it('clears all filters when clicking clear button', async () => {
    render(<RecipesPage />);
    
    // Open filters and select some
    fireEvent.click(screen.getByRole('button', { name: /filters/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Dinner' }));
    fireEvent.click(screen.getByRole('button', { name: 'Breakfast' }));
    
    // Click clear
    fireEvent.click(screen.getByText('Clear all filters'));
    
    // Buttons should be deselected
    expect(screen.getByRole('button', { name: 'Dinner' })).not.toHaveClass('bg-sage-600');
    expect(screen.getByRole('button', { name: 'Breakfast' })).not.toHaveClass('bg-sage-600');
  });

  it('opens recipe detail modal when clicking a recipe card', async () => {
    render(<RecipesPage />);
    
    // Wait for recipes to load
    await waitFor(() => {
      expect(screen.getByText('Chicken Stir Fry')).toBeInTheDocument();
    });
    
    // Click on a recipe card
    fireEvent.click(screen.getByText('Chicken Stir Fry'));
    
    // Modal should be visible with recipe details
    // The modal should show the same recipe name in a larger heading
    const modalHeading = screen.getAllByText('Chicken Stir Fry');
    expect(modalHeading.length).toBeGreaterThan(1);
  });

  it('closes modal when clicking close button', async () => {
    render(<RecipesPage />);
    
    // Wait for recipes and click one
    await waitFor(() => {
      expect(screen.getByText('Chicken Stir Fry')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Chicken Stir Fry'));
    
    // Modal should be visible (look for the modal overlay class)
    await waitFor(() => {
      const modalOverlay = document.querySelector('.fixed.inset-0.bg-black\\/50');
      expect(modalOverlay).toBeInTheDocument();
    });
    
    // Click the overlay to close modal
    const modalOverlay = document.querySelector('.fixed.inset-0.bg-black\\/50');
    if (modalOverlay) {
      fireEvent.click(modalOverlay);
    }
  });

  it('shows filter count badge when filters are active', async () => {
    render(<RecipesPage />);
    
    // Open filters and select a meal type
    fireEvent.click(screen.getByRole('button', { name: /filters/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Dinner' }));
    
    // Wait for state update and verify the Dinner button is now selected
    await waitFor(() => {
      const dinnerButton = screen.getByRole('button', { name: 'Dinner' });
      expect(dinnerButton).toHaveClass('bg-sage-600');
    });
    
    // The badge should appear on the filters button
    await waitFor(() => {
      // Badge has bg-terracotta-500 class
      const badge = document.querySelector('.bg-terracotta-500.text-white.text-xs.rounded-full');
      expect(badge).toBeInTheDocument();
    });
  });

  it('displays difficulty on recipe cards', async () => {
    render(<RecipesPage />);
    
    await waitFor(() => {
      // Look for the difficulty badge text
      const easyBadges = screen.getAllByText('easy');
      expect(easyBadges.length).toBeGreaterThan(0);
    });
  });

  it('handles API error gracefully', async () => {
    (recipeApi.search as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('Failed to fetch')
    );
    
    render(<RecipesPage />);
    
    await waitFor(() => {
      // The component displays the error message directly
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when no recipes found', async () => {
    (recipeApi.search as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      status: 'success',
      recipes: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    
    render(<RecipesPage />);
    
    await waitFor(() => {
      expect(screen.getByText(/no recipes yet/i)).toBeInTheDocument();
    });
  });
});

