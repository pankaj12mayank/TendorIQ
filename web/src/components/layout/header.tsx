'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Moon, Sun, ChevronRight } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useState, useCallback, useMemo } from 'react';

import { useCurrentUser, useSignOut } from '@/hooks/use-auth';
import { getPageTitle } from '@/lib/page-titles';
import { SignOutDialog } from '@/components/auth/sign-out-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

export function Header() {
  const pathname = usePathname();
  const user = useCurrentUser();
  const signOut = useSignOut();
  const { theme, setTheme } = useTheme();
  const [signOutOpen, setSignOutOpen] = useState(false);

  const pageTitle = getPageTitle(pathname);
  const initials = useMemo(() => {
    if (!user?.name) return 'U';
    return user.name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, [user?.name]);

  const handleConfirmSignOut = useCallback(async () => {
    await signOut();
  }, [signOut]);

  return (
    <header className="nav-glass sticky top-0 z-sticky flex h-[4.25rem] items-center justify-between gap-3 px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <Link
          href="/dashboard"
          className="hidden shrink-0 text-muted-foreground transition-colors hover:text-foreground sm:inline"
        >
          Home
        </Link>
        <ChevronRight className="hidden h-4 w-4 shrink-0 text-muted-foreground/60 sm:block" />
        <h2 className="truncate font-display text-base font-semibold tracking-tight md:text-lg">
          {pageTitle}
        </h2>
      </div>

      <div className="flex shrink-0 items-center gap-1.5">
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9 rounded-lg"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          aria-label="Toggle theme"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-10 gap-2 rounded-full pl-1 pr-2">
              <Avatar className="h-8 w-8 ring-2 ring-border/80">
                <AvatarImage src={user?.imageUrl} alt={user?.name ?? 'User'} />
                <AvatarFallback className="bg-primary/10 text-xs font-semibold text-primary">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <span className="hidden max-w-[8rem] truncate text-sm font-medium lg:inline">
                {user?.name?.split(' ')[0]}
              </span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="px-3 py-2.5">
              <p className="text-sm font-medium">{user?.name}</p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => setSignOutOpen(true)}
              className="text-destructive focus:text-destructive"
            >
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <SignOutDialog
        open={signOutOpen}
        onOpenChange={setSignOutOpen}
        onConfirm={handleConfirmSignOut}
      />
    </header>
  );
}
