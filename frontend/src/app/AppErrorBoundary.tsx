import { useRouteError } from "react-router-dom";

export function AppErrorBoundary() {
  const error = useRouteError();
  const message =
    error instanceof Error ? error.message : "An unexpected application error occurred.";

  return (
    <main className="shell" role="alert">
      <h1>Application unavailable</h1>
      <p>{message}</p>
    </main>
  );
}
