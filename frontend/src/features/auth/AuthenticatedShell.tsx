import { useState } from "react";
import { Link, Outlet } from "react-router-dom";

import { useAuth } from "./useAuth";

export function AuthenticatedShell() {
  const { logout, user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleLogout() {
    setSubmitting(true);
    setError(null);
    try {
      await logout();
    } catch {
      setError("Sign out could not be confirmed. Please retry.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="application-shell">
      <header className="app-topbar">
        <Link className="brand" to="/">
          Project-X
        </Link>
        <div className="user-menu">
          <h1 className="welcome-title">Welcome, {user?.display_name}</h1>
          <span className="role-badge">{user?.role}</span>
          <button
            className="secondary-button"
            disabled={submitting}
            onClick={() => void handleLogout()}
            type="button"
          >
            {submitting ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </header>
      {error && (
        <p className="auth-error shell-error" role="alert">
          {error}
        </p>
      )}
      {user?.role === "ADMIN" && (
        <nav aria-label="Administrator" className="admin-nav">
          <Link to="/admin">Overview</Link>
          <Link to="/admin/institution">Institution</Link>
          <Link to="/admin/classrooms">Classrooms</Link>
          <Link to="/admin/cameras">Cameras</Link>
        </nav>
      )}
      <Outlet />
    </div>
  );
}
