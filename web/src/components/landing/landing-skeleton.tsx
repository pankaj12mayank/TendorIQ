export function LandingSkeleton() {
  return (
    <div className="min-h-screen animate-pulse bg-background">
      <div className="h-16 border-b border-border/40" />
      <div className="mx-auto max-w-4xl px-4 pt-32 space-y-6">
        <div className="h-12 w-3/4 rounded-lg bg-muted" />
        <div className="h-6 w-full rounded bg-muted" />
        <div className="h-6 w-2/3 rounded bg-muted" />
        <div className="flex gap-4 pt-4">
          <div className="h-12 w-36 rounded-lg bg-muted" />
          <div className="h-12 w-36 rounded-lg bg-muted" />
        </div>
      </div>
    </div>
  );
}
