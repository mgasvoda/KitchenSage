/**
 * ToastContext - Global state management for toast notifications
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ToastContainer, type ToastType, type ToastProps } from '../components/Toast';

interface ToastContextType {
  showToast: (config: Omit<ToastProps, 'id' | 'onDismiss'>) => string;
  updateToast: (id: string, updates: Partial<Omit<ToastProps, 'id' | 'onDismiss'>>) => void;
  dismissToast: (id: string) => void;
  showProcessing: (message: string) => string;
  showSuccess: (message: string, actionLabel?: string, onAction?: () => void) => string;
  showError: (message: string, onRetry?: () => void) => string;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Array<ToastProps>>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((config: Omit<ToastProps, 'id' | 'onDismiss'>) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    const newToast: ToastProps = {
      ...config,
      id,
      onDismiss: dismissToast,
    };
    setToasts((prev) => [...prev, newToast]);
    return id;
  }, [dismissToast]);

  const updateToast = useCallback((id: string, updates: Partial<Omit<ToastProps, 'id' | 'onDismiss'>>) => {
    setToasts((prev) =>
      prev.map((toast) =>
        toast.id === id
          ? { ...toast, ...updates }
          : toast
      )
    );
  }, []);

  const showProcessing = useCallback((message: string) => {
    return showToast({
      type: 'processing',
      message,
      autoDismiss: false,
    });
  }, [showToast]);

  const showSuccess = useCallback((message: string, actionLabel?: string, onAction?: () => void) => {
    return showToast({
      type: 'success',
      message,
      actionLabel,
      onAction,
      autoDismiss: true,
      dismissAfter: 5000,
    });
  }, [showToast]);

  const showError = useCallback((message: string, onRetry?: () => void) => {
    return showToast({
      type: 'error',
      message,
      onRetry,
      autoDismiss: true,
      dismissAfter: 7000,
    });
  }, [showToast]);

  return (
    <ToastContext.Provider
      value={{
        showToast,
        updateToast,
        dismissToast,
        showProcessing,
        showSuccess,
        showError,
      }}
    >
      {children}
      <ToastContainer toasts={toasts} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
