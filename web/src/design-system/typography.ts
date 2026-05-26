/** Typography utility class maps */
export const typography = {
  display: 'font-display text-4xl md:text-5xl font-semibold tracking-tight text-foreground',
  h1: 'font-display text-3xl font-semibold tracking-tight text-foreground',
  h2: 'font-display text-2xl font-semibold tracking-tight text-foreground',
  h3: 'text-lg font-semibold tracking-tight text-foreground',
  h4: 'text-base font-medium text-foreground',
  body: 'text-sm text-foreground leading-relaxed',
  bodyMuted: 'text-sm text-muted-foreground leading-relaxed',
  caption: 'text-xs text-muted-foreground',
  label: 'text-xs font-medium uppercase tracking-wider text-muted-foreground',
  tableHead: 'text-xs font-medium text-muted-foreground',
  tableCell: 'text-sm text-foreground',
  sidebarItem: 'text-sm font-medium',
  kpiValue: 'font-display text-3xl font-semibold tracking-tight tabular-nums',
  kpiLabel: 'text-sm font-medium text-muted-foreground',
} as const;
