import { StrictMode } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";

import { AuthProvider } from "../auth/AuthContext";
import { App } from "../../pages/App";
import type { AuthUser } from "../auth/types";
import type { Camera, Classroom, Institution } from "./types";

const institution: Institution = {
  id: "inst-1",
  name: "Demo College",
  code: "DEMO",
  timezone: "Asia/Kolkata",
  is_active: true,
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-01T00:00:00Z",
};

const admin: AuthUser = {
  id: "admin-1",
  email: "admin@example.invalid",
  display_name: "Demo Admin",
  role: "ADMIN",
  is_active: true,
  institution_id: institution.id,
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function page<T>(results: T[]) {
  return { count: results.length, next: null, previous: null, results };
}

function installApi() {
  const classrooms: Classroom[] = [];
  const cameras: Camera[] = [];
  const requests: Array<{ path: string; method: string; body?: Record<string, unknown> }> = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), "http://localhost");
    const path = url.pathname;
    const method = init?.method ?? "GET";
    const body = init?.body
      ? (JSON.parse(String(init.body)) as Record<string, unknown>)
      : undefined;
    requests.push({ path, method, body });

    if (path.endsWith("/auth/csrf/")) return jsonResponse({ csrf_token: "csrf-test" });
    if (path.endsWith("/auth/refresh")) {
      return jsonResponse({ error: { message: "Authentication is required." } }, 401);
    }
    if (path.endsWith("/auth/login")) return jsonResponse({ access: "access-test", user: admin });
    if (path.endsWith("/auth/me")) return jsonResponse(admin);
    if (path === "/api/v1/institutions/" && method === "GET")
      return jsonResponse(page([institution]));
    if (path === `/api/v1/institutions/${institution.id}/`) return jsonResponse(institution);

    if (path === "/api/v1/classrooms/" && method === "GET") {
      const search = url.searchParams.get("search")?.toLowerCase() ?? "";
      return jsonResponse(
        page(classrooms.filter((room) => room.code.toLowerCase().includes(search))),
      );
    }
    if (path === "/api/v1/classrooms/" && method === "POST" && body) {
      const room: Classroom = {
        id: "room-1",
        institution: { id: institution.id, code: institution.code, name: institution.name },
        code: String(body.code),
        name: String(body.name ?? ""),
        capacity: typeof body.capacity === "number" ? body.capacity : null,
        is_active: true,
        created_at: "2026-10-04T00:00:00Z",
        updated_at: "2026-10-04T00:00:00Z",
      };
      classrooms.push(room);
      return jsonResponse(room, 201);
    }
    if (path === "/api/v1/classrooms/room-1/") return jsonResponse(classrooms[0]);

    if (path === "/api/v1/cameras/" && method === "GET") {
      const classroomId = url.searchParams.get("classroom_id");
      return jsonResponse(
        page(cameras.filter((camera) => !classroomId || camera.classroom_id === classroomId)),
      );
    }
    if (path === "/api/v1/cameras/" && method === "POST" && body) {
      const camera: Camera = {
        id: "camera-1",
        code: String(body.code),
        display_name: String(body.display_name),
        classroom_id: String(body.classroom_id),
        classroom: { id: "room-1", code: "CSE-301", name: "" },
        source_type: "LOCAL_FILE",
        status: "ACTIVE",
        resolution: typeof body.resolution === "string" ? body.resolution : null,
        frame_rate: typeof body.frame_rate === "number" ? body.frame_rate : null,
        description: String(body.description ?? ""),
        created_at: "2026-10-04T00:00:00Z",
        updated_at: "2026-10-04T00:00:00Z",
      };
      cameras.push(camera);
      return jsonResponse(camera, 201);
    }
    if (path === "/api/v1/cameras/camera-1/") return jsonResponse(cameras[0]);
    return jsonResponse({ error: { message: `Unexpected API request: ${method} ${path}` } }, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  return requests;
}

function renderApp(initialEntry = "/login") {
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

async function loginAsAdmin() {
  fireEvent.change(await screen.findByLabelText("Email"), {
    target: { value: "admin@example.invalid" },
  });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "demo-password" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  expect(await screen.findByRole("heading", { name: "Infrastructure overview" })).toBeVisible();
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("administrator infrastructure flow", () => {
  it("shows live institution and infrastructure counts from the API", async () => {
    installApi();
    renderApp();
    await loginAsAdmin();

    expect(await screen.findByText("Demo College")).toBeVisible();
    expect(screen.getByText("0 active · connection status is not monitored")).toBeVisible();
    expect(screen.getByRole("link", { name: "Institution" })).toBeVisible();
  });

  it("creates a classroom then registers a LOCAL_FILE camera under it", async () => {
    const requests = installApi();
    renderApp();
    await loginAsAdmin();
    fireEvent.click(screen.getByRole("link", { name: "Classrooms" }));

    fireEvent.change(await screen.findByLabelText("Room code"), { target: { value: "CSE-301" } });
    fireEvent.change(screen.getByLabelText(/Capacity/), { target: { value: "45" } });
    fireEvent.click(screen.getByRole("button", { name: "Create classroom" }));
    expect(await screen.findByRole("heading", { name: "CSE-301" })).toBeVisible();

    fireEvent.click(screen.getByRole("link", { name: "Register camera" }));
    fireEvent.change(await screen.findByLabelText("Camera code"), {
      target: { value: "CAM-CSE-301-01" },
    });
    fireEvent.change(screen.getByLabelText("Display name"), { target: { value: "Front" } });
    fireEvent.change(screen.getAllByLabelText("Classroom")[1], {
      target: { value: "room-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Register camera" }));
    expect(await screen.findByRole("heading", { name: "CAM-CSE-301-01" })).toBeVisible();
    expect(screen.getByText(/status below is metadata status, not online status/i)).toBeVisible();

    const classroomCreate = requests.find(
      (request) => request.path === "/api/v1/classrooms/" && request.method === "POST",
    );
    const cameraCreate = requests.find(
      (request) => request.path === "/api/v1/cameras/" && request.method === "POST",
    );
    expect(classroomCreate?.body).toMatchObject({ code: "CSE-301", capacity: 45 });
    expect(classroomCreate?.body).not.toHaveProperty("institution_id");
    expect(cameraCreate?.body).toMatchObject({
      code: "CAM-CSE-301-01",
      classroom_id: "room-1",
      source_type: "LOCAL_FILE",
    });
  });

  it("renders the institution context without a create action", async () => {
    installApi();
    renderApp();
    await loginAsAdmin();
    fireEvent.click(screen.getByRole("link", { name: "Institution" }));
    expect(await screen.findByLabelText("Institution name")).toHaveValue("Demo College");
    expect(screen.queryByRole("button", { name: /create institution/i })).not.toBeInTheDocument();
  });
});
