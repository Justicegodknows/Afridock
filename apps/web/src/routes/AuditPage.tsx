import { PageContainer } from "../components/layout/PageContainer";
import { useHasCapability } from "../hooks/useHasCapability";
import { auditLogExportUrl, useAuditLog } from "../services/usage";

function formatCost(costUsd: number): string {
  return costUsd === 0 ? "$0.00" : `$${costUsd.toFixed(4)}`;
}

/**
 * Plan E6: an exportable, immutable record of who used what, when, and at
 * what cost. Admin-only (see api/routes/usage.py) — matches "Viewers cannot
 * access the audit export" (and Users can't either: this is the raw
 * per-request trail, not the aggregate cost dashboard at /usage).
 */
export function AuditPage() {
  const { data: entries, isLoading, isError } = useAuditLog();
  const canView = useHasCapability("audit.view");

  if (!canView) {
    return (
      <PageContainer>
        <p className="text-sm text-text-muted">Only Admins can view the audit log.</p>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-heading text-xl">
          Audit log{entries ? ` · ${entries.length}` : ""}
        </h3>
        <a
          href={auditLogExportUrl()}
          className="inline-flex items-center justify-center gap-1.5 rounded-md px-4 py-2 font-heading text-sm font-semibold text-text-muted transition-colors hover:text-text"
        >
          Export CSV
        </a>
      </div>

      {isLoading && <p className="text-sm text-text-muted">Loading audit log…</p>}
      {isError && <p className="text-sm text-red-600">Couldn&apos;t load the audit log.</p>}
      {entries && entries.length === 0 && (
        <p className="text-sm text-text-muted">No activity yet.</p>
      )}
      {entries && entries.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="text-text-subtle">
            <tr>
              <th className="pb-2 font-medium">User</th>
              <th className="pb-2 font-medium">Model</th>
              <th className="pb-2 font-medium">Tokens</th>
              <th className="pb-2 font-medium">Cost</th>
              <th className="pb-2 font-medium">Latency</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 font-medium">When</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-divider">
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td className="py-2.5 text-text-muted">{entry.userEmail ?? "—"}</td>
                <td className="py-2.5 font-heading text-[15px]">{entry.modelProfile}</td>
                <td className="py-2.5 text-text-muted">{entry.totalTokens.toLocaleString()}</td>
                <td className="py-2.5 text-text-muted">{formatCost(entry.costUsd)}</td>
                <td className="py-2.5 text-text-muted">
                  {entry.latencyMs !== null ? `${entry.latencyMs}ms` : "—"}
                </td>
                <td className="py-2.5">
                  {entry.status === "error" ? (
                    <span className="text-xs text-red-600">Error</span>
                  ) : (
                    <span className="text-xs text-text-muted">OK</span>
                  )}
                </td>
                <td className="py-2.5 text-xs text-text-subtle">
                  {new Date(entry.createdAt).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PageContainer>
  );
}
