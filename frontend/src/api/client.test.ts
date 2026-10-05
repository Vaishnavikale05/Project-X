import { afterEach, describe, expect, it, vi } from "vitest";

import { apiRequest } from "./client";

afterEach(() => vi.unstubAllGlobals());

describe("API client", () => {
  it("maps the shared error envelope into a safe ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            error: { message: "Authentication is required.", request_id: "request-1" },
          }),
          { status: 401, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(apiRequest("/private")).rejects.toMatchObject({
      status: 401,
      requestId: "request-1",
    });
  });
});
