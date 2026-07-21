import { useQuery } from "@tanstack/react-query";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

type HealthResponse = { status: string };

async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/healthz`);
  if (!response.ok) {
    throw new Error(`API health check failed: ${response.status}`);
  }
  return response.json();
}

/** Small always-visible smoke test (Phase 0 AC: "web shell loads... shows
 * API status") — moved from the old ChatPage header into the sidebar
 * footer now that AppShell owns a uniform header across every page. */
export function ApiStatusIndicator() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    retry: false,
    refetchInterval: 30_000,
  });

  const color = isLoading ? "bg-text-subtle" : isError ? "bg-red-500" : "bg-accent";
  const label = isLoading ? "checking API…" : isError ? "API unreachable" : `API ${data?.status}`;

  return (
    <span className="flex items-center gap-1.5 text-[11px] text-text-subtle" title={label}>
      <span className={`h-1.5 w-1.5 rounded-full ${color}`} />
      API
    </span>
  );
}
