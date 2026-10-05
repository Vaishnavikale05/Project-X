import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "./useAuth";

export function RequireAuth() {
  const { error, retrySession, status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <main className="auth-state" role="status">
        Loading your session…
      </main>
    );
  }
  if (status === "error") {
    return (
      <main className="auth-state">
        <p role="alert">{error}</p>
        <button onClick={() => void retrySession()} type="button">
          Retry
        </button>
      </main>
    );
  }
  if (status !== "authenticated") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}
