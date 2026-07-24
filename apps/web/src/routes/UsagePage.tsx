import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardBody, CardKicker, CardTitle } from "../components/ui/card";
import { useUsageSummary } from "../services/usage";

function StatTile({ kicker, value }: { kicker: string; value: string }) {
  return (
    <Card className="flex-1">
      <CardKicker>{kicker}</CardKicker>
      <CardTitle>{value}</CardTitle>
    </Card>
  );
}

function formatCost(costUsd: number): string {
  return costUsd === 0 ? "$0.00" : `$${costUsd.toFixed(4)}`;
}

/**
 * Plan E6/E10: token volume, spend, and per-model cost breakdown. The bar
 * chart is a single series (cost per model profile) — magnitude by
 * category, one hue (the app's accent token), no legend needed since the
 * title names the series and each bar is already directly labeled by its
 * x-axis category.
 */
export function UsagePage() {
  const { data: summary, isLoading, isError } = useUsageSummary();

  if (isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-text-muted">Loading usage…</p>
      </PageContainer>
    );
  }

  if (isError || !summary) {
    return (
      <PageContainer>
        <p className="text-sm text-red-600">Couldn&apos;t load usage data.</p>
      </PageContainer>
    );
  }

  const chartData = summary.byProfile.map((row) => ({
    name: row.modelProfile,
    costUsd: row.costUsd,
    totalTokens: row.totalTokens,
  }));

  return (
    <PageContainer>
      <div className="mb-6 flex gap-3.5">
        <StatTile kicker="Total tokens" value={summary.totalTokens.toLocaleString()} />
        <StatTile kicker="Total cost" value={formatCost(summary.totalCostUsd)} />
        <StatTile kicker="Requests" value={summary.requestCount.toLocaleString()} />
      </div>

      <Card className="mb-6">
        <CardKicker>Low-cost AI · #1 design constraint</CardKicker>
        <CardTitle>Cost by model</CardTitle>
        <CardBody>
          Open-source and self-hosted models (Ollama, Hugging Face, vLLM) always cost $0 here —
          only an explicitly enabled commercial fallback ever shows a real dollar figure.
        </CardBody>
        {chartData.length === 0 ? (
          <p className="mt-2 text-sm text-text-muted">No usage yet.</p>
        ) : (
          <div className="mt-2 h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-divider)" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "var(--color-text-muted)", fontSize: 12 }}
                  tickLine={false}
                  axisLine={{ stroke: "var(--color-divider)" }}
                />
                <YAxis
                  tick={{ fill: "var(--color-text-muted)", fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value: number) => `$${value}`}
                />
                <Tooltip
                  formatter={(value) => formatCost(Number(value))}
                  contentStyle={{
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-divider)",
                    borderRadius: 6,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="costUsd" fill="var(--color-accent)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <table className="w-full text-left text-sm">
        <thead className="text-text-subtle">
          <tr>
            <th className="pb-2 font-medium">Model</th>
            <th className="pb-2 font-medium">Requests</th>
            <th className="pb-2 font-medium">Tokens</th>
            <th className="pb-2 font-medium">Cost</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-divider">
          {summary.byProfile.map((row) => (
            <tr key={row.modelProfile}>
              <td className="py-2.5 font-heading text-[15px]">{row.modelProfile}</td>
              <td className="py-2.5 text-text-muted">{row.requestCount.toLocaleString()}</td>
              <td className="py-2.5 text-text-muted">{row.totalTokens.toLocaleString()}</td>
              <td className="py-2.5 text-text-muted">{formatCost(row.costUsd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </PageContainer>
  );
}
