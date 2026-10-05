import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { ApiError } from "../../api/client";
import { useAuth } from "./useAuth";

export function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status === "authenticated") return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      const requestedPath = (location.state as { from?: string } | null)?.from;
      const destination =
        requestedPath?.startsWith("/") && !requestedPath.startsWith("//") ? requestedPath : "/";
      navigate(destination, { replace: true });
    } catch (cause) {
      setError(
        cause instanceof ApiError && cause.status === 401
          ? "Invalid email or password."
          : cause instanceof Error
            ? cause.message
            : "Sign in could not be completed.",
      );
    } finally {
      setSubmitting(false);
      setPassword("");
    }
  }

  return (
    <main className="auth-page">
      <section aria-labelledby="login-title" className="auth-card">
        <p className="eyebrow">Classroom Engagement Analytics</p>
        <h1 id="login-title">Sign in to Project-X</h1>
        <p className="auth-description">Use your college-managed account to continue.</p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="email">Email</label>
          <input
            autoComplete="username"
            id="email"
            name="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
          <label htmlFor="password">Password</label>
          <input
            autoComplete="current-password"
            id="password"
            name="password"
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          {error && (
            <p className="auth-error" role="alert">
              {error}
            </p>
          )}
          <button disabled={submitting || status === "loading"} type="submit">
            {submitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
