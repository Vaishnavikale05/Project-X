interface AsyncStateProps {
  loading: boolean;
  error?: string;
  children: React.ReactNode;
}

export function AsyncState({ loading, error, children }: AsyncStateProps) {
  if (loading) return <p role="status">Loading…</p>;
  if (error) return <p role="alert">{error}</p>;
  return <>{children}</>;
}
