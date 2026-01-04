/**
 * useTaskPolling - Custom hook for polling async task status
 * 
 * Polls a task endpoint until the task completes (success or failure)
 */

import { useEffect, useRef, useCallback } from 'react';
import { groceryListApi } from '../services/api';

export interface UseTaskPollingOptions {
  taskId: string | null;
  onSuccess?: (result: any) => void;
  onError?: (error: string) => void;
  pollingInterval?: number;
  enabled?: boolean;
}

export function useTaskPolling({
  taskId,
  onSuccess,
  onError,
  pollingInterval = 2000,
  enabled = true,
}: UseTaskPollingOptions) {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);

  const checkTaskStatus = useCallback(async () => {
    if (!taskId || !enabled || isPollingRef.current) {
      return;
    }

    isPollingRef.current = true;

    try {
      const response = await groceryListApi.getTaskStatus(taskId);
      const task = response.task;

      if (task.status === 'completed') {
        // Stop polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        
        // Call success callback
        if (onSuccess && task.result) {
          onSuccess(task.result);
        }
      } else if (task.status === 'failed') {
        // Stop polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        
        // Call error callback
        if (onError) {
          onError(task.error || 'Task failed');
        }
      }
      // If status is 'pending' or 'processing', continue polling
    } catch (error) {
      console.error('Error polling task status:', error);
      
      // On network error, stop polling and call error callback
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      
      if (onError) {
        onError(error instanceof Error ? error.message : 'Failed to check task status');
      }
    } finally {
      isPollingRef.current = false;
    }
  }, [taskId, enabled, onSuccess, onError]);

  useEffect(() => {
    if (!taskId || !enabled) {
      return;
    }

    // Start polling immediately
    checkTaskStatus();

    // Then poll at intervals
    intervalRef.current = setInterval(checkTaskStatus, pollingInterval);

    // Cleanup on unmount or when taskId changes
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [taskId, enabled, pollingInterval, checkTaskStatus]);

  return {
    isPolling: !!intervalRef.current,
  };
}
