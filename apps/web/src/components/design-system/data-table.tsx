'use client';

import type { ReactNode } from 'react';

import { cn } from '@/lib/utils';

export function DataTableShell({
  title,
  description,
  toolbar,
  children,
  footer,
  className,
}: {
  title?: string;
  description?: string;
  toolbar?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('surface-card overflow-hidden', className)}>
      {(title || toolbar) && (
        <div className="flex flex-col gap-3 border-b border-border/60 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            {title && <h3 className="font-display text-base font-semibold">{title}</h3>}
            {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
          </div>
          {toolbar && <div className="flex flex-wrap items-center gap-2">{toolbar}</div>}
        </div>
      )}
      <div className="scroll-premium overflow-x-auto">{children}</div>
      {footer && <div className="border-t border-border/60 p-4">{footer}</div>}
    </div>
  );
}

export function DataTable({ className, ...props }: React.TableHTMLAttributes<HTMLTableElement>) {
  return <table className={cn('w-full caption-bottom text-sm', className)} {...props} />;
}

export function DataTableHeader({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={cn(
        'sticky top-0 z-10 bg-muted/50 backdrop-blur-sm [&_tr]:border-b [&_tr]:border-border/60',
        className
      )}
      {...props}
    />
  );
}

export function DataTableHead({ className, ...props }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={cn(
        'h-11 px-4 text-left align-middle text-xs font-medium uppercase tracking-wider text-muted-foreground',
        className
      )}
      {...props}
    />
  );
}

export function DataTableBody({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={cn('[&_tr:last-child]:border-0', className)} {...props} />;
}

export function DataTableRow({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={cn(
        'border-b border-border/40 transition-colors hover:bg-muted/40 data-[state=selected]:bg-muted',
        className
      )}
      {...props}
    />
  );
}

export function DataTableCell({ className, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn('p-4 align-middle text-sm', className)} {...props} />;
}
