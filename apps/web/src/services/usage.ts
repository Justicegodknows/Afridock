import { useQuery } from "@tanstack/react-query";

import { http } from "../lib/api/http";

export type UsageByProfile = {
  modelProfile: string;
  totalTokens: number;
  costUsd: number;
  requestCount: number;
};

export type UsageSummary = {
  totalTokens: number;
  totalCostUsd: number;
  requestCount: number;
  byProfile: UsageByProfile[];
};

export type AuditLogEntry = {
  id: string;
  userEmail: string | null;
  modelProfile: string;
  litellmModel: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  costUsd: number;
  latencyMs: number | null;
  status: string;
  createdAt: string;
};

export function useUsageSummary() {
  return useQuery({
    queryKey: ["usage", "summary"],
    queryFn: () => http.get<UsageSummary>("/organizations/current/usage"),
  });
}

export function useAuditLog() {
  return useQuery({
    queryKey: ["usage", "audit"],
    queryFn: () => http.get<AuditLogEntry[]>("/organizations/current/audit"),
  });
}

const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

/** A plain navigation (not `http.get`, which always parses JSON) — the
 * browser handles the CSV download/Content-Disposition itself. */
export function auditLogExportUrl(): string {
  return `${API_BASE_URL}/organizations/current/audit/export.csv`;
}
