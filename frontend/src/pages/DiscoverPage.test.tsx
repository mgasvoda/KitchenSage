/**
 * Tests for DiscoverPage component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '../test/test-utils';
import { DiscoverPage } from './DiscoverPage';
import { pendingRecipeApi } from '../services/api';
import type { PendingRecipe } from '../types';

// Mock the API
vi.mock('../services/api', () => ({
  pendingRecipeApi: {
    parseUrl: vi.fn(),
    discover: vi.fn(),
    list: vi.fn(),
    get: vi.fn(),
    update: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
  },
}));

const mockPendingRecipe: PendingRecipe = {
  id: 1,
  name: 'Test Recipe',
  description: 'A test recipe',
  prep_time: 10,
  cook_time: 20,
  servings: 4,
  difficulty: 'Easy',
  cuisine: 'Italian',
  dietary_tags: ['vegetarian'],
  ingredients: [
    { name: 'flour', quantity: 2, unit: 'cups' },
    { name: 'water', quantity: 1, unit: 'cup' },
  ],
  instructions: ['Step 1', 'Step 2'],
  status: 'pending',
  source_url: 'https://example.com/recipe',
  created_at: '2024-01-01T00:00:00Z',
};

describe('DiscoverPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Tab Rendering', () => {
    it('renders three tabs', () => {
      render(<DiscoverPage />);
      
      expect(screen.getByText('Add by URL')).toBeInTheDocument();
      expect(screen.getByText('AI Search')).toBeInTheDocument();
      expect(screen.getByText(/Pending Review/)).toBeInTheDocument();
    });
  });

  describe('URL Parser', () => {
    it('renders URL parser form', () => {
      render(<DiscoverPage />);
      
      const urlInput = screen.getByPlaceholderText(/https:\/\/example.com\/recipe/);
      expect(urlInput).toBeInTheDocument();
      expect(screen.getByText('Parse Recipe')).toBeInTheDocument();
    });

    it('submits URL and parses recipe', async () => {
      vi.mocked(pendingRecipeApi.parseUrl).mockResolvedValue({
        status: 'success',
        message: 'Recipe parsed successfully',
        pending_recipe: mockPendingRecipe,
      });
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const urlInput = screen.getByPlaceholderText(/https:\/\/example.com\/recipe/);
      const submitButton = screen.getByText('Parse Recipe');
      
      fireEvent.change(urlInput, { target: { value: 'https://example.com/recipe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(pendingRecipeApi.parseUrl).toHaveBeenCalledWith('https://example.com/recipe');
      });
    });

    it('displays parsed recipe card', async () => {
      vi.mocked(pendingRecipeApi.parseUrl).mockResolvedValue({
        status: 'success',
        message: 'Recipe parsed successfully',
        pending_recipe: mockPendingRecipe,
      });
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const urlInput = screen.getByPlaceholderText(/https:\/\/example.com\/recipe/);
      const submitButton = screen.getByText('Parse Recipe');
      
      fireEvent.change(urlInput, { target: { value: 'https://example.com/recipe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      });
    });

    it('displays error message on parse failure', async () => {
      vi.mocked(pendingRecipeApi.parseUrl).mockRejectedValue(new Error('Failed to parse URL'));
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const urlInput = screen.getByPlaceholderText(/https:\/\/example.com\/recipe/);
      const submitButton = screen.getByText('Parse Recipe');
      
      fireEvent.change(urlInput, { target: { value: 'https://invalid-url.com' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Failed to parse URL/i)).toBeInTheDocument();
      });
    });

    it('handles duplicate detection', async () => {
      vi.mocked(pendingRecipeApi.parseUrl).mockResolvedValue({
        status: 'duplicate',
        message: 'A recipe from this URL is already pending review',
        pending_recipe: mockPendingRecipe,
      });
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const urlInput = screen.getByPlaceholderText(/https:\/\/example.com\/recipe/);
      const submitButton = screen.getByText('Parse Recipe');
      
      fireEvent.change(urlInput, { target: { value: 'https://example.com/recipe' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/already pending review/i)).toBeInTheDocument();
      });
    });
  });

  describe('AI Search', () => {
    it('renders AI search form', () => {
      render(<DiscoverPage />);
      
      // Click on AI Search tab
      const searchTab = screen.getByText('AI Search');
      fireEvent.click(searchTab);
      
      expect(screen.getByPlaceholderText(/quick weeknight pasta/i)).toBeInTheDocument();
      expect(screen.getByText('Discover Recipes')).toBeInTheDocument();
    });

    it('submits search query', async () => {
      vi.mocked(pendingRecipeApi.discover).mockResolvedValue({
        status: 'success',
        message: 'Found 1 recipes',
        pending_recipes: [mockPendingRecipe],
        query: 'pasta',
      });
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const searchTab = screen.getByText('AI Search');
      fireEvent.click(searchTab);
      
      const queryInput = screen.getByPlaceholderText(/quick weeknight pasta/i);
      const submitButton = screen.getByText('Discover Recipes');
      
      fireEvent.change(queryInput, { target: { value: 'pasta recipes' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(pendingRecipeApi.discover).toHaveBeenCalledWith({
          query: 'pasta recipes',
          cuisine: undefined,
          dietary_restrictions: undefined,
          max_results: 5,
        });
      });
    });

    it('applies cuisine and dietary filters', async () => {
      vi.mocked(pendingRecipeApi.discover).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        query: 'pasta',
      });
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const searchTab = screen.getByText('AI Search');
      fireEvent.click(searchTab);
      
      // Select cuisine - find select element
      const cuisineSelects = screen.getAllByRole('combobox');
      const cuisineSelect = cuisineSelects.find(select => 
        select.textContent?.includes('cuisine') || select.getAttribute('name')?.includes('cuisine')
      ) || cuisineSelects[0];
      if (cuisineSelect) {
        fireEvent.change(cuisineSelect, { target: { value: 'italian' } });
      }
      
      // Toggle dietary restriction
      const vegetarianButton = screen.getByText(/vegetarian/i);
      fireEvent.click(vegetarianButton);
      
      const queryInput = screen.getByPlaceholderText(/quick weeknight pasta/i);
      const submitButton = screen.getByText('Discover Recipes');
      
      fireEvent.change(queryInput, { target: { value: 'pasta' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(pendingRecipeApi.discover).toHaveBeenCalledWith({
          query: 'pasta',
          cuisine: 'italian',
          dietary_restrictions: ['vegetarian'],
          max_results: 5,
        });
      });
    });

    it('displays discovered recipes', async () => {
      vi.mocked(pendingRecipeApi.discover).mockResolvedValue({
        status: 'success',
        message: 'Found 2 recipes',
        pending_recipes: [
          mockPendingRecipe,
          { ...mockPendingRecipe, id: 2, name: 'Recipe 2' },
        ],
        query: 'pasta',
      });
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const searchTab = screen.getByText('AI Search');
      fireEvent.click(searchTab);
      
      const queryInput = screen.getByPlaceholderText(/quick weeknight pasta/i);
      const submitButton = screen.getByText('Discover Recipes');
      
      fireEvent.change(queryInput, { target: { value: 'pasta' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('Test Recipe')).toBeInTheDocument();
        expect(screen.getByText('Recipe 2')).toBeInTheDocument();
      });
    });

    it('displays search error', async () => {
      vi.mocked(pendingRecipeApi.discover).mockRejectedValue(new Error('Search failed'));
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const searchTab = screen.getByText('AI Search');
      fireEvent.click(searchTab);
      
      const queryInput = screen.getByPlaceholderText(/quick weeknight pasta/i);
      const submitButton = screen.getByText('Discover Recipes');
      
      fireEvent.change(queryInput, { target: { value: 'pasta' } });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/Search failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Pending Queue', () => {
    it('loads and displays pending recipes', async () => {
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [mockPendingRecipe],
        total: 1,
      });

      render(<DiscoverPage />);
      
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);

      await waitFor(() => {
        expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      });
    });

    it('displays empty state when no pending recipes', async () => {
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);

      await waitFor(() => {
        expect(screen.getByText(/All caught up!/i)).toBeInTheDocument();
      });
    });

    it('refreshes pending list', async () => {
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);
      
      const refreshButton = screen.getByText('Refresh');
      fireEvent.click(refreshButton);

      await waitFor(() => {
        expect(pendingRecipeApi.list).toHaveBeenCalledTimes(2); // Initial load + refresh
      });
    });
  });

  describe('Recipe Actions', () => {
    beforeEach(() => {
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [mockPendingRecipe],
        total: 1,
      });
    });

    it('approves recipe', async () => {
      vi.mocked(pendingRecipeApi.approve).mockResolvedValue({
        status: 'success',
        message: 'Recipe approved',
        recipe_id: 1,
      });

      render(<DiscoverPage />);
      
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);

      await waitFor(() => {
        expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      });

      const approveButton = screen.getByText('Approve');
      fireEvent.click(approveButton);

      await waitFor(() => {
        expect(pendingRecipeApi.approve).toHaveBeenCalledWith(1);
      });
    });

    it('rejects recipe', async () => {
      vi.mocked(pendingRecipeApi.reject).mockResolvedValue({
        status: 'success',
        message: 'Recipe rejected',
      });

      render(<DiscoverPage />);
      
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);

      await waitFor(() => {
        expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      });

      const rejectButton = screen.getByText('Reject');
      fireEvent.click(rejectButton);

      await waitFor(() => {
        expect(pendingRecipeApi.reject).toHaveBeenCalledWith(1);
      });
    });

    it('opens edit modal', async () => {
      render(<DiscoverPage />);
      
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);

      await waitFor(() => {
        expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      });

      const editButton = screen.getByText('Edit');
      fireEvent.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });
    });

    it('saves edited recipe', async () => {
      vi.mocked(pendingRecipeApi.update).mockResolvedValue({
        status: 'success',
        message: 'Recipe updated',
        pending_recipe: { ...mockPendingRecipe, name: 'Updated Recipe' },
      });

      render(<DiscoverPage />);
      
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);

      await waitFor(() => {
        expect(screen.getByText('Test Recipe')).toBeInTheDocument();
      });

      const editButton = screen.getByText('Edit');
      fireEvent.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });

      // Find name input - it should be the first text input in the modal
      const nameInputs = screen.getAllByRole('textbox');
      const nameInput = nameInputs[0] || screen.getByDisplayValue('Test Recipe');
      fireEvent.change(nameInput, { target: { value: 'Updated Recipe' } });

      const saveButton = screen.getByText('Save Changes');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(pendingRecipeApi.update).toHaveBeenCalled();
      });
    });
  });

  describe('Tab Switching', () => {
    it('switches between tabs', () => {
      render(<DiscoverPage />);
      
      // Start on URL tab
      expect(screen.getByPlaceholderText(/https:\/\/example.com\/recipe/)).toBeInTheDocument();
      
      // Switch to search tab
      const searchTab = screen.getByText('AI Search');
      fireEvent.click(searchTab);
      expect(screen.getByPlaceholderText(/quick weeknight pasta/i)).toBeInTheDocument();
      
      // Switch to pending tab
      const pendingTab = screen.getByText(/Pending Review/);
      fireEvent.click(pendingTab);
      expect(screen.getByText(/Recipes Awaiting Review/i)).toBeInTheDocument();
    });
  });

  describe('Loading States', () => {
    it('shows loading indicator while parsing', async () => {
      vi.mocked(pendingRecipeApi.parseUrl).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          status: 'success',
          pending_recipe: mockPendingRecipe,
        }), 100))
      );
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const urlInput = screen.getByPlaceholderText(/https:\/\/example.com\/recipe/);
      const submitButton = screen.getByText('Parse Recipe');
      
      fireEvent.change(urlInput, { target: { value: 'https://example.com/recipe' } });
      fireEvent.click(submitButton);

      expect(screen.getByText('Parsing...')).toBeInTheDocument();
    });

    it('shows loading indicator while searching', async () => {
      vi.mocked(pendingRecipeApi.discover).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({
          status: 'success',
          pending_recipes: [],
        }), 100))
      );
      vi.mocked(pendingRecipeApi.list).mockResolvedValue({
        status: 'success',
        pending_recipes: [],
        total: 0,
      });

      render(<DiscoverPage />);
      
      const searchTab = screen.getByText('AI Search');
      fireEvent.click(searchTab);
      
      const queryInput = screen.getByPlaceholderText(/quick weeknight pasta/i);
      const submitButton = screen.getByText('Discover Recipes');
      
      fireEvent.change(queryInput, { target: { value: 'pasta' } });
      fireEvent.click(submitButton);

      expect(screen.getByText('Searching...')).toBeInTheDocument();
    });
  });
});

