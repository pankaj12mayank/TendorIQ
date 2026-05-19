'use client';

import { useState, createContext, useContext, useCallback, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  success: (title: string, message?: string) => void;
  error: (title: string, message?: string) => void;
  warning: (title: string, message?: string) => void;
  info: (title: string, message?: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { ...toast, id }]);
    
    // Auto remove after duration
    setTimeout(() => removeToast(id), toast.duration || 5000);
  }, [removeToast]);

  const success = useCallback((title: string, message?: string) => 
    addToast({ type: 'success', title, message }), [addToast]);
  
  const error = useCallback((title: string, message?: string) => 
    addToast({ type: 'error', title, message }), [addToast]);
  
  const warning = useCallback((title: string, message?: string) => 
    addToast({ type: 'warning', title, message }), [addToast]);
  
  const info = useCallback((title: string, message?: string) => 
    addToast({ type: 'info', title, message }), [addToast]);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
}

function ToastContainer({ toasts, onRemove }: { toasts: Toast[]; onRemove: (id: string) => void }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      <AnimatePresence>
        {toasts.map(toast => (
          <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
        ))}
      </AnimatePresence>
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
  const icons = {
    success: <CheckCircle className="w-5 h-5 text-green-500" />,
    error: <AlertCircle className="w-5 h-5 text-red-500" />,
    warning: <AlertTriangle className="w-5 h-5 text-yellow-500" />,
    info: <Info className="w-5 h-5 text-blue-500" />,
  };

  const colors = {
    success: 'border-green-500 bg-green-500/10',
    error: 'border-red-500 bg-red-500/10',
    warning: 'border-yellow-500 bg-yellow-500/10',
    info: 'border-blue-500 bg-blue-500/10',
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 100 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 100 }}
      className={`flex items-start gap-3 p-4 rounded-lg border ${colors[toast.type]} shadow-lg backdrop-blur-sm`}
    >
      {icons[toast.type]}
      <div className="flex-1">
        <p className="font-semibold text-sm">{toast.title}</p>
        {toast.message && <p className="text-xs text-muted-foreground mt-1">{toast.message}</p>}
      </div>
      <button onClick={() => onRemove(toast.id)} className="text-muted-foreground hover:text-foreground">
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
}

// Pre-built notification helpers for common scenarios
export const notifications = {
  planActivated: (planName: string) => ({
    type: 'success' as ToastType,
    title: '🎉 Plan Activated!',
    message: `Your ${planName} plan is now active!`
  }),
  planUpgraded: (planName: string) => ({
    type: 'success' as ToastType,
    title: '🚀 Plan Upgraded!',
    message: `You've upgraded to ${planName}. Enjoy new features!`
  }),
  paymentSuccess: (amount: string) => ({
    type: 'success' as ToastType,
    title: '💳 Payment Successful!',
    message: `Payment of ${amount} received. Thank you!`
  }),
  paymentFailed: () => ({
    type: 'error' as ToastType,
    title: '❌ Payment Failed',
    message: 'Please check your payment method and try again.'
  }),
  userAdded: (name: string, role: string) => ({
    type: 'info' as ToastType,
    title: '👤 Team Member Added',
    message: `${name} joined as ${role}`
  }),
  analysisComplete: (tenderName: string) => ({
    type: 'success' as ToastType,
    title: '🔍 Analysis Complete',
    message: `AI analysis for "${tenderName}" is ready!`
  }),
  welcome: () => ({
    type: 'success' as ToastType,
    title: '👋 Welcome to TenderIQ!',
    message: "Let's get started with your first tender."
  }),
};

export default ToastProvider;