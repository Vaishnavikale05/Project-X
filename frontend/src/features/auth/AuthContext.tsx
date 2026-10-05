import { useCallback, useEffect, useMemo, useState, type PropsWithChildren } from "react";

import { ApiError } from "../../api/client";
import * as authApi from "./api";
import { AuthContext } from "./auth-context";
import type { AuthStatus, AuthUser } from "./types";

export interface AuthContextValue {
  accessToken: string | null;
  status: AuthStatus;
  user: AuthUser | null;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  retrySession: () => Promise<void>;
}

function expiryDelayMs(token: string): number {
  try {
    const payload = token.split(".")[1];
    if (!payload) return 240_000;
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const claims = JSON.parse(window.atob(base64)) as { exp?: number };
    if (!claims.exp) return 240_000;
    return Math.min(2_147_000_000, Math.max(1_000, claims.exp * 1_000 - Date.now() - 30_000));
  } catch {
    return 240_000;
  }
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<AuthUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const restoreSession = useCallback(async () => {
    setStatus("loading");
    setError(null);
    try {
      const { access } = await authApi.refresh();
      const current = await authApi.currentUser(access);
      setAccessToken(access);
      setUser(current);
      setStatus("authenticated");
    } catch (cause) {
      setAccessToken(null);
      setUser(null);
      if (cause instanceof ApiError && cause.status === 401) {
        setStatus("anonymous");
        setError(null);
      } else {
        setStatus("error");
        setError("The authentication service is unavailable. Try again.");
      }
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function loadInitialSession() {
      try {
        const { access } = await authApi.refresh();
        const current = await authApi.currentUser(access);
        if (!active) return;
        setAccessToken(access);
        setUser(current);
        setStatus("authenticated");
      } catch (cause) {
        if (!active) return;
        setAccessToken(null);
        setUser(null);
        if (cause instanceof ApiError && cause.status === 401) {
          setStatus("anonymous");
        } else {
          setStatus("error");
          setError("The authentication service is unavailable. Try again.");
        }
      }
    }
    void loadInitialSession();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (status !== "authenticated" || !accessToken) return undefined;
    const timeout = window.setTimeout(() => void restoreSession(), expiryDelayMs(accessToken));
    return () => window.clearTimeout(timeout);
  }, [accessToken, restoreSession, status]);

  const loginUser = useCallback(async (email: string, password: string) => {
    setError(null);
    const result = await authApi.login(email, password);
    const current = await authApi.currentUser(result.access);
    setAccessToken(result.access);
    setUser(current);
    setStatus("authenticated");
  }, []);

  const logoutUser = useCallback(async () => {
    await authApi.logout();
    setAccessToken(null);
    setUser(null);
    setError(null);
    setStatus("anonymous");
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      accessToken,
      status,
      user,
      error,
      login: loginUser,
      logout: logoutUser,
      retrySession: restoreSession,
    }),
    [accessToken, error, loginUser, logoutUser, restoreSession, status, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
