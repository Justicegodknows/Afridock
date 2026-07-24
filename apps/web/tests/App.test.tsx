import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "../src/App";

describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the Afrikdock heading once the session resolves", async () => {
    // AuthGuard calls GET /users/me on mount (hooks/useAuthBootstrap.ts) —
    // stub a valid session so the protected shell (and its "Afrikdock"
    // heading) actually renders instead of staying on the loading/redirect
    // state.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          id: "11111111-1111-1111-1111-111111111111",
          email: "demo@example.com",
          is_active: true,
          is_superuser: false,
          is_verified: true,
          org_id: "22222222-2222-2222-2222-222222222222",
          role: "admin",
          display_name: null,
        }),
      }),
    );

    const queryClient = new QueryClient();
    render(
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>,
    );

    expect(await screen.findByText("Afrikdock")).toBeInTheDocument();
  });
});
