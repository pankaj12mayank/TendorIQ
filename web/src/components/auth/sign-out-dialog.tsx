'use client';

import { useState, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';

interface SignOutDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void | Promise<void>;
}

export function SignOutDialog({ open, onOpenChange, onConfirm }: SignOutDialogProps) {
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  async function handleConfirm() {
    setLoading(true);
    try {
      await onConfirm();
    } finally {
      setLoading(false);
      onOpenChange(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/50"
        aria-label="Close"
        onClick={() => onOpenChange(false)}
      />
      <div
        role="alertdialog"
        aria-labelledby="signout-title"
        className="relative z-10 w-full max-w-md rounded-xl border bg-card p-6 shadow-xl"
      >
        <h2 id="signout-title" className="text-lg font-semibold">
          Are you sure you want to sign out?
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          You will need to sign in again to access your dashboard.
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={() => void handleConfirm()} disabled={loading}>
            {loading ? 'Signing out...' : 'Sign out'}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function SignOutButton({
  children,
  onSignOut,
  className,
}: {
  children: ReactNode;
  onSignOut: () => void | Promise<void>;
  className?: string;
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button type="button" className={className} onClick={() => setOpen(true)}>
        {children}
      </button>
      <SignOutDialog open={open} onOpenChange={setOpen} onConfirm={onSignOut} />
    </>
  );
}
