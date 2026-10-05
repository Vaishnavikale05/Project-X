import { apiRequest } from "../../api/client";
import type {
  Camera,
  CameraInput,
  Classroom,
  ClassroomInput,
  Institution,
  InstitutionInput,
  Page,
} from "./types";

function get<T>(token: string, path: string): Promise<T> {
  return apiRequest<T>(path, { headers: { Authorization: `Bearer ${token}` } });
}

function send<T>(token: string, path: string, method: string, body: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const infrastructureApi = {
  institutions(token: string): Promise<Page<Institution>> {
    return get(token, "/institutions/?page_size=100");
  },
  institution(token: string, id: string): Promise<Institution> {
    return get(token, `/institutions/${encodeURIComponent(id)}/`);
  },
  updateInstitution(token: string, id: string, input: InstitutionInput): Promise<Institution> {
    return send(token, `/institutions/${encodeURIComponent(id)}/`, "PATCH", input);
  },
  classrooms(
    token: string,
    params: { search?: string; is_active?: boolean; page?: number; page_size?: number } = {},
  ): Promise<Page<Classroom>> {
    const query = new URLSearchParams({ page_size: String(params.page_size ?? 25) });
    if (params.search) query.set("search", params.search);
    if (params.is_active !== undefined) query.set("is_active", String(params.is_active));
    if (params.page) query.set("page", String(params.page));
    return get(token, `/classrooms/?${query.toString()}`);
  },
  classroom(token: string, id: string): Promise<Classroom> {
    return get(token, `/classrooms/${encodeURIComponent(id)}/`);
  },
  createClassroom(token: string, input: ClassroomInput): Promise<Classroom> {
    return send(token, "/classrooms/", "POST", input);
  },
  updateClassroom(token: string, id: string, input: ClassroomInput): Promise<Classroom> {
    return send(token, `/classrooms/${encodeURIComponent(id)}/`, "PATCH", input);
  },
  cameras(
    token: string,
    params: { classroom_id?: string; search?: string; status?: string; page?: number } = {},
  ): Promise<Page<Camera>> {
    const query = new URLSearchParams({ page_size: "25" });
    if (params.classroom_id) query.set("classroom_id", params.classroom_id);
    if (params.search) query.set("search", params.search);
    if (params.status) query.set("status", params.status);
    if (params.page) query.set("page", String(params.page));
    return get(token, `/cameras/?${query.toString()}`);
  },
  camera(token: string, id: string): Promise<Camera> {
    return get(token, `/cameras/${encodeURIComponent(id)}/`);
  },
  createCamera(token: string, input: CameraInput): Promise<Camera> {
    return send(token, "/cameras/", "POST", input);
  },
  updateCamera(token: string, id: string, input: CameraInput): Promise<Camera> {
    return send(token, `/cameras/${encodeURIComponent(id)}/`, "PATCH", input);
  },
};

export function errorMessage(error: unknown): string {
  if (error && typeof error === "object" && "details" in error) {
    const details = (error as { details?: unknown }).details;
    if (typeof details === "string") return details;
    if (details && typeof details === "object") {
      const messages = Object.values(details as Record<string, unknown>)
        .flatMap((value) => (Array.isArray(value) ? value : [value]))
        .filter((value): value is string => typeof value === "string");
      if (messages.length) return messages.join(" ");
    }
  }
  if (error instanceof Error) return error.message;
  return "The request could not be completed. Try again.";
}
