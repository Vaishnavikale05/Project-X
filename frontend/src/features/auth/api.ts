import { apiRequest } from "../../api/client";
import type { AuthUser, LoginResponse, RefreshResponse } from "./types";

let refreshInFlight: Promise<RefreshResponse> | null = null;

async function csrfHeaders(): Promise<HeadersInit> {
  const { csrf_token: csrfToken } = await apiRequest<{ csrf_token: string }>("/auth/csrf/");
  return { "Content-Type": "application/json", "X-CSRFToken": csrfToken };
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    headers: await csrfHeaders(),
    body: JSON.stringify({ email, password }),
  });
}

export async function refresh(): Promise<RefreshResponse> {
  if (!refreshInFlight) {
    refreshInFlight = (async () =>
      apiRequest<RefreshResponse>("/auth/refresh", {
        method: "POST",
        headers: await csrfHeaders(),
        body: "{}",
      }))().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

export async function logout(): Promise<void> {
  await apiRequest<void>("/auth/logout", {
    method: "POST",
    headers: await csrfHeaders(),
    body: "{}",
  });
}

export async function currentUser(accessToken: string): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}
