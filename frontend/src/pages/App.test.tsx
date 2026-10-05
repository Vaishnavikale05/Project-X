import { StrictMode } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { AuthProvider } from "../features/auth/AuthContext";
import type { AuthUser } from "../features/auth/types";
import { App } from "./App";

const user: AuthUser = {
  id: "user-1",
  email: "teacher@example.invalid",
  display_name: "Demo Teacher",
  role: "TEACHER",
  is_active: true,
  institution_id: "institution-1",
};

const accessToken = `e30.${btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + 300 }))}.signature`;

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function apiError(status: number, detail = "Authentication is required.") {
  return jsonResponse(
    {
      error: {
        code: "not_authenticated",
        message: "Authentication is required.",
        details: { detail },
        request_id: "request-1",
      },
    },
    status,
  );
}

function installAuthApi(options?: { existingSession?: boolean; loginStatus?: number }) {
  const requests: Array<{ path: string; init?: RequestInit }> = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = new URL(String(input), "http://localhost").pathname;
    requests.push({ path, init });
    if (path.endsWith("/auth/csrf/")) return jsonResponse({ csrf_token: "csrf-test-token" });
    if (path.endsWith("/auth/refresh")) {
      return options?.existingSession ? jsonResponse({ access: accessToken }) : apiError(401);
    }
    if (path.endsWith("/auth/login")) {
      if (options?.loginStatus && options.loginStatus !== 200) {
        return apiError(options.loginStatus, "Invalid email or password.");
      }
      return jsonResponse({ access: accessToken, user });
    }
    if (path.endsWith("/auth/me")) return jsonResponse(user);
    if (path.endsWith("/auth/logout")) return new Response(null, { status: 204 });
    return jsonResponse({}, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return requests;
}

function renderApp(initialEntry = "/") {
  return render(
    <StrictMode>
      <AuthProvider>
        <MemoryRouter initialEntries={[initialEntry]}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </StrictMode>,
  );
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("authentication flow", () => {
  it("redirects an unauthenticated visitor to the login form", async () => {
    installAuthApi();
    renderApp();

    expect(await screen.findByRole("heading", { name: "Sign in to Project-X" })).toBeVisible();
    expect(screen.getByLabelText("Email")).toBeVisible();
    expect(screen.getByLabelText("Password")).toBeVisible();
  });

  it("restores a browser session, loads current user, and displays the role", async () => {
    const requests = installAuthApi({ existingSession: true });
    renderApp();

    expect(await screen.findByRole("heading", { name: "Welcome, Demo Teacher" })).toBeVisible();
    expect(requests.filter(({ path }) => path.endsWith("/auth/refresh"))).toHaveLength(1);
    expect(requests.some(({ path }) => path.endsWith("/auth/me"))).toBe(true);
    expect(screen.getByText("TEACHER")).toBeVisible();
  });

  it("logs in, loads the current user, and opens the protected route", async () => {
    const requests = installAuthApi();
    renderApp("/login");
    fireEvent.change(await screen.findByLabelText("Email"), {
      target: { value: "teacher@example.invalid" },
    });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "demo-passphrase" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("heading", { name: "Welcome, Demo Teacher" })).toBeVisible();
    const currentUserRequest = requests.find(({ path }) => path.endsWith("/auth/me"));
    expect(currentUserRequest?.init?.headers).toMatchObject({
      Authorization: `Bearer ${accessToken}`,
    });
    expect(requests.some(({ path }) => path.endsWith("/auth/login"))).toBe(true);
  });

  it("shows a generic error for invalid credentials", async () => {
    installAuthApi({ loginStatus: 401 });
    renderApp("/login");
    fireEvent.change(await screen.findByLabelText("Email"), {
      target: { value: "missing@example.invalid" },
    });
    fireEvent.change(screen.getByLabelText("Password"), { target: { value: "wrong-passphrase" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid email or password.");
  });

  it("logs out and returns to the login route", async () => {
    const requests = installAuthApi({ existingSession: true });
    renderApp();
    fireEvent.click(await screen.findByRole("button", { name: "Sign out" }));

    expect(await screen.findByRole("heading", { name: "Sign in to Project-X" })).toBeVisible();
    expect(requests.some(({ path }) => path.endsWith("/auth/logout"))).toBe(true);
  });

  it("shows a retry state if the authentication service is unavailable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    renderApp();

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "authentication service is unavailable",
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
  });
});
