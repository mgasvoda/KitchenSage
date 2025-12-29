/**
 * Toast - Notification component for bottom-right corner
 * 
 * Displays status messages for async operations with auto-dismiss
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export type ToastType = 'processing' | 'success' | 'error';

export interface ToastProps {
  id: string;
  type: ToastType;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  onRetry?: () => void;
  onDismiss: (id: string) => void;
  autoDismiss?: boolean;
  dismissAfter?: number;
}

export function Toast({
  id,
  type,
  message,
  actionLabel,
  onAction,
  onRetry,
  onDismiss,
  autoDismiss = true,
  dismissAfter = 5000,
}: ToastProps) {
  const navigate = useNavigate();

  useEffect(() => {
    if (autoDismiss && (type === 'success' || type === 'error')) {
      const timer = setTimeout(() => {
        onDismiss(id);
      }, dismissAfter);
      return () => clearTimeout(timer);
    }
  }, [id, type, autoDismiss, dismissAfter, onDismiss]);

  const getIcon = () => {
    switch (type) {
      case 'processing':
        return (
          <div className="animate-spin rounded-full h-5 w-5 border-2 border-sage-600 border-t-transparent"></div>
        );
      case 'success':
        return (
          <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'error':
        return (
          <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
    }
  };

  const getStyles = () => {
    switch (type) {
      case 'processing':
        return 'bg-white border-sage-200 text-sage-800';
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
    }
  };

  const handleViewGroceryList = () => {
    navigate('/grocery');
    onDismiss(id);
  };

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg border-2 ${getStyles()} min-w-[320px] max-w-md animate-slide-in`}
      role="alert"
    >
      <div className="flex-shrink-0 mt-0.5">{getIcon()}</div>
      
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium">{message}</p>
        
        {/* Action buttons */}
        {(onAction || onRetry || actionLabel) && (
          <div className="mt-2 flex gap-2">
            {type === 'success' && actionLabel && (
              <button
                onClick={actionLabel === 'View Grocery List' ? handleViewGroceryList : onAction}
                className="text-xs font-semibold text-sage-700 hover:text-sage-800 underline"
              >
                {actionLabel}
              </button>
            )}
            {type === 'error' && onRetry && (
              <button
                onClick={onRetry}
                className="text-xs font-semibold text-red-700 hover:text-red-800 underline"
              >
                Retry
              </button>
            )}
          </div>
        )}
      </div>

      {/* Dismiss button (not shown for processing) */}
      {type !== 'processing' && (
        <button
          onClick={() => onDismiss(id)}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Dismiss"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
}

/**
 * ToastContainer - Container for rendering multiple toasts
 */
export interface ToastContainerProps {
  toasts: Array<ToastProps>;
}

export function ToastContainer({ toasts }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} />
      ))}
    </div>
  );
}
