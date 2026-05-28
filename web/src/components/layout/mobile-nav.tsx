'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useSignOut, useCurrentUser } from '@/hooks/use-auth';
import { SignOutDialog } from '@/components/auth/sign-out-dialog';
import { getNavGroupsForUser } from '@/lib/nav-role';

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const [signOutOpen, setSignOutOpen] = useState(false);
  const pathname = usePathname();
  const signOut = useSignOut();
  const user = useCurrentUser();

  const navigation = useMemo(() => getNavGroupsForUser(user).flatMap((g) => g.items), [user]);

  useEffect(() => {
    if (!isOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = prev;
    };
  }, [isOpen]);

  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  return (
    <div className="lg:hidden">
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 z-40 h-10 w-10 rounded-full border border-border/70 bg-background/95 shadow-sm backdrop-blur"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close navigation menu' : 'Open navigation menu'}
        aria-expanded={isOpen}
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </Button>
      {isOpen && (
        <nav className="fixed inset-0 z-30 overflow-y-auto bg-background/98 p-6 pb-8 pt-16 backdrop-blur-xl">
          <ul className="space-y-2">
            {navigation.map((item) => (
              <li key={item.href}>
                {(() => {
                  const isActive =
                    item.href === '/dashboard'
                      ? pathname === '/dashboard'
                      : pathname === item.href || pathname.startsWith(`${item.href}/`);
                  return (
                <Link
                  href={item.href}
                  className={cn(
                    'block rounded-md px-3 py-2 text-sm font-medium',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                  onClick={() => setIsOpen(false)}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {item.name}
                </Link>
                  );
                })()}
              </li>
            ))}
          </ul>
          <Button variant="outline" className="mt-6 w-full" onClick={() => setSignOutOpen(true)}>
            Sign out
          </Button>
        </nav>
      )}
      <SignOutDialog open={signOutOpen} onOpenChange={setSignOutOpen} onConfirm={signOut} />
    </div>
  );
}
