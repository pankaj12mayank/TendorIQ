import * as React from 'react';
import { cn } from '@/lib/utils';

interface PaginationProps extends React.HTMLAttributes<HTMLDivElement> {}

const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  ({ className, ...props }, ref) => (
    <nav
      ref={ref}
      className={cn('mx-auto flex w-full justify-center', className)}
      aria-label="pagination"
      {...props}
    />
  )
);
Pagination.displayName = 'Pagination';

const PaginationContent = React.forwardRef<HTMLUListElement, React.HTMLAttributes<HTMLUListElement>>(
  ({ className, ...props }, ref) => (
    <ul
      ref={ref}
      className={cn('flex flex-row items-center gap-1', className)}
      {...props}
    />
  )
);
PaginationContent.displayName = 'PaginationContent';

const PaginationItem = React.forwardRef<HTMLLIElement, React.HTMLAttributes<HTMLLIElement>>(
  ({ className, ...props }, ref) => (
    <li ref={ref} className={cn('', className)} {...props} />
  )
);
PaginationItem.displayName = 'PaginationItem';

const PaginationLink = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<'button'> & { isActive?: boolean }
>(({ className, isActive, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        'inline-flex h-9 min-w-9 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors hover:bg-muted disabled:pointer-events-none disabled:opacity-50 sm:h-10 sm:min-w-10',
        isActive
          ? 'border-primary bg-primary text-primary-foreground'
          : 'border-muted bg-background hover:bg-muted hover:text-foreground',
        className
      )}
      aria-current={isActive ? 'page' : undefined}
      {...props}
    />
  )
);
PaginationLink.displayName = 'PaginationLink';

const PaginationPrevious = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<typeof PaginationLink>
>(({ className, ...props }, ref) => (
  <PaginationLink
    ref={ref}
    className={cn('w-auto gap-1 px-2.5 sm:px-3.5', className)}
    {...props}
  >
    <span>Previous</span>
  </PaginationLink>
));
PaginationPrevious.displayName = 'PaginationPrevious';

const PaginationNext = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<typeof PaginationLink>
>(({ className, ...props }, ref) => (
  <PaginationLink
    ref={ref}
    className={cn('w-auto gap-1 px-2.5 sm:px-3.5', className)}
    {...props}
  >
    <span>Next</span>
  </PaginationLink>
));
PaginationNext.displayName = 'PaginationNext';

export {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
};