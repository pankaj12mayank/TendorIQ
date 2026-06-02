import { cn } from '@/lib/utils';

interface LoadingStateProps {
  message?: string;
  fullScreen?: boolean;
}

export function LoadingState({ message = 'Loading...', fullScreen = false }: LoadingStateProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <div className="flex items-center justify-center">
        <div className={cn('h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent')} />
      </div>
      <p className="text-muted-foreground">{message}</p>
    </div>
  );

  if (fullScreen) {
    return <div className="flex min-h-screen items-center justify-center">{content}</div>;
  }

  return content;
}
