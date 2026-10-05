export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: unknown;
    request_id: string | null;
  };
}

export interface HealthResponse {
  status: "ok" | "degraded";
  dependencies: Record<string, "ok" | "unavailable">;
  request_id: string | null;
}
