/**
 * Tests for API client, specifically pendingRecipeApi.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { pendingRecipeApi } from './api';
import type { PendingRecipe } from '../types';

// Mock fetch globally
global.fetch = vi.fn();

describe('pendingRecipeApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('parseUrl', () => {
    it('successfully parses URL', async () => {
      const mockResponse: any = {
        status: 'success',
        message: 'Recipe parsed successfully',
        pending_recipe: {
          id: 1,
          name: 'Test Recipe',
          status: 'pending',
        },
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.parseUrl('https://example.com/recipe');

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes/parse',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ url: 'https://example.com/recipe' }),
        })
      );
      expect(result.status).toBe('success');
      expect(result.pending_recipe).toBeDefined();
    });

    it('handles parse errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Failed to parse URL' }),
      } as Response);

      await expect(pendingRecipeApi.parseUrl('https://invalid-url.com')).rejects.toThrow();
    });

    it('handles network errors', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));

      await expect(pendingRecipeApi.parseUrl('https://example.com/recipe')).rejects.toThrow('Network error');
    });
  });

  describe('discover', () => {
    it('successfully discovers recipes', async () => {
      const mockResponse: any = {
        status: 'success',
        message: 'Found 2 recipes',
        pending_recipes: [
          { id: 1, name: 'Recipe 1' },
          { id: 2, name: 'Recipe 2' },
        ],
        query: 'pasta',
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.discover({
        query: 'pasta recipes',
        cuisine: 'Italian',
        dietary_restrictions: ['vegetarian'],
        max_results: 5,
      });

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes/discover',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            query: 'pasta recipes',
            cuisine: 'Italian',
            dietary_restrictions: ['vegetarian'],
            max_results: 5,
          }),
        })
      );
      expect(result.status).toBe('success');
      expect(result.pending_recipes).toHaveLength(2);
    });

    it('handles discovery with minimal params', async () => {
      const mockResponse: any = {
        status: 'success',
        pending_recipes: [],
        query: 'pasta',
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.discover({
        query: 'pasta',
      });

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes/discover',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            query: 'pasta',
          }),
        })
      );
      expect(result.status).toBe('success');
    });

    it('handles discovery errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Discovery failed' }),
      } as Response);

      await expect(
        pendingRecipeApi.discover({ query: 'nonexistent' })
      ).rejects.toThrow();
    });
  });

  describe('list', () => {
    it('successfully lists pending recipes', async () => {
      const mockResponse: any = {
        status: 'success',
        pending_recipes: [
          { id: 1, name: 'Recipe 1' },
          { id: 2, name: 'Recipe 2' },
        ],
        total: 2,
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.list(50);

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes?limit=50',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result.status).toBe('success');
      expect(result.pending_recipes).toHaveLength(2);
    });

    it('lists without limit parameter', async () => {
      const mockResponse: any = {
        status: 'success',
        pending_recipes: [],
        total: 0,
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.list();

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result.status).toBe('success');
    });
  });

  describe('get', () => {
    it('successfully gets a pending recipe', async () => {
      const mockResponse: any = {
        status: 'success',
        pending_recipe: {
          id: 1,
          name: 'Test Recipe',
          status: 'pending',
        },
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.get(1);

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes/1',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
      expect(result.status).toBe('success');
      expect(result.pending_recipe.id).toBe(1);
    });

    it('handles 404 error', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Pending recipe not found' }),
      } as Response);

      await expect(pendingRecipeApi.get(999)).rejects.toThrow();
    });
  });

  describe('update', () => {
    it('successfully updates a pending recipe', async () => {
      const mockResponse: any = {
        status: 'success',
        message: 'Pending recipe updated',
        pending_recipe: {
          id: 1,
          name: 'Updated Recipe',
        },
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const updateData = {
        name: 'Updated Recipe',
        prep_time: 15,
      };

      const result = await pendingRecipeApi.update(1, updateData);

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      );
      expect(result.status).toBe('success');
      expect(result.pending_recipe.name).toBe('Updated Recipe');
    });

    it('handles update errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Pending recipe not found' }),
      } as Response);

      await expect(
        pendingRecipeApi.update(999, { name: 'New Name' })
      ).rejects.toThrow();
    });
  });

  describe('approve', () => {
    it('successfully approves a pending recipe', async () => {
      const mockResponse: any = {
        status: 'success',
        message: 'Recipe approved',
        recipe_id: 1,
        pending_id: 1,
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.approve(1);

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes/1/approve',
        expect.objectContaining({
          method: 'POST',
        })
      );
      expect(result.status).toBe('success');
      expect(result.recipe_id).toBe(1);
    });

    it('handles approval errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Failed to approve recipe' }),
      } as Response);

      await expect(pendingRecipeApi.approve(1)).rejects.toThrow();
    });
  });

  describe('reject', () => {
    it('successfully rejects a pending recipe', async () => {
      const mockResponse: any = {
        status: 'success',
        message: 'Recipe rejected',
      };

      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const result = await pendingRecipeApi.reject(1);

      expect(fetch).toHaveBeenCalledWith(
        '/api/pending-recipes/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
      expect(result.status).toBe('success');
    });

    it('handles rejection errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Pending recipe not found' }),
      } as Response);

      await expect(pendingRecipeApi.reject(999)).rejects.toThrow();
    });
  });

  describe('error handling', () => {
    it('handles network errors', async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'));

      await expect(pendingRecipeApi.list()).rejects.toThrow('Network error');
    });

    it('handles 500 server errors', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ message: 'Internal server error' }),
      } as Response);

      await expect(pendingRecipeApi.list()).rejects.toThrow();
    });

    it('handles malformed JSON responses', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON');
        },
      } as Response);

      await expect(pendingRecipeApi.list()).rejects.toThrow();
    });
  });
});

