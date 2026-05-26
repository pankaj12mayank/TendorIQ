'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useSignOut, useCurrentUser } from '@/hooks/use-auth';
import { SignOutDialog } from '@/components/auth/sign-out-dialog';
import { getNavGroupsForUser } from '@/lib/nav-role';
import { ROUTES } from '@/lib/routes';

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false);
  const [signOutOpen, setSignOutOpen] = useState(false);
  const pathname = usePathname();
  const signOut = useSignOut();
  const user = useCurrentUser();

  const navigation = useMemo(() => getNavGroupsForUser(user).flatMap((g) => g.items), [user]);

  return (
    <div className="lg:hidden">
      <Button
        variant="ghost"
        size="icon"
        className="fixed left-4 top-4 z-40"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </Button>
      {isOpen && (
        <nav className="fixed inset-0 z-30 bg-background/98 p-6 pt-16 backdrop-blur-xl">
          <ul className="space-y-2">
            {navigation.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'block rounded-md px-3 py-2 text-sm font-medium',
                    pathname === item.href || pathname.startsWith(`${item.href}/`)
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )}
                  onClick={() => setIsOpen(false)}
                >
                  {item.name}
                </Link>
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
