import { Spinner } from './spinner';

interface LoadingStateProps {
  message?: string;
  fullScreen?: boolean;
}

export function LoadingState({ message = 'Loading...', fullScreen = false }: LoadingStateProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-4 p-8">
      <Spinner size="lg" />
      <p className="text-muted-foreground">{message}</p>
    </div>
  );

  if (fullScreen) {
    return <div className="flex min-h-screen items-center justify-center">{content}</div>;
  }

  return content;
}