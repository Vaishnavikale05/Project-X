const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly requestId?: string,
    readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    credentials: init?.credentials ?? "same-origin",
    headers: { Accept: "application/json", ...init?.headers },
  });

  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    const errorBody = payload as {
      error?: { message?: string; request_id?: string; details?: unknown };
    } | null;
    throw new ApiError(
      errorBody?.error?.message ?? "The API request failed.",
      response.status,
      errorBody?.error?.request_id,
      errorBody?.error?.details,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
