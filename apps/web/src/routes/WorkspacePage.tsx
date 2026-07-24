import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardBody, CardKicker, CardTitle } from "../components/ui/card";
import { useHasCapability } from "../hooks/useHasCapability";
import { useCurrentOrganization, useUpdateOrganizationSettings } from "../services/organization";

/**
 * Reachable from the sidebar's WorkspaceSwitcher (⚙ link), not the primary
 * nav — the mockup has no dedicated "Organization" nav item, only a
 * workspace-create dialog, so profile editing for the *current* workspace
 * lives here instead of competing for a spot among the mockup's 10 items.
 */
export function WorkspacePage() {
  const { data: org, isLoading } = useCurrentOrganization();
  const updateSettings = useUpdateOrganizationSettings();
  const canManage = useHasCapability("org_settings.manage");

  return (
    <PageContainer>
      <div className="max-w-[560px] space-y-4">
        <Card>
          <CardKicker>Workspace</CardKicker>
          <CardTitle>{isLoading ? "…" : org?.name}</CardTitle>
        </Card>

        <Card>
          <CardKicker>Low-cost AI · #1 design constraint</CardKicker>
          <CardTitle>Commercial model fallback</CardTitle>
          <CardBody>
            By default, Afridock only ever falls back across free, open-source, self-hosted
            models (Llama, Mixtral). Enabling this lets it escalate to a commercial provider
            (Claude/OpenAI) as a last resort when every open-source option fails — which carries
            a real per-token cost. Leave off unless you&apos;ve accepted that trade-off.
          </CardBody>
          {canManage ? (
            <label className="mt-2 flex items-center gap-2.5 text-sm">
              <input
                type="checkbox"
                checked={org?.allowCommercialFallback ?? false}
                disabled={isLoading || updateSettings.isPending}
                onChange={(event) => updateSettings.mutate(event.target.checked)}
                className="h-4 w-4 rounded border-divider accent-accent"
              />
              Allow commercial fallback (may incur real cost)
            </label>
          ) : (
            <p className="mt-2 text-xs text-text-subtle">
              {org?.allowCommercialFallback
                ? "Commercial fallback is enabled for this organization."
                : "Commercial fallback is disabled for this organization."}{" "}
              Only Admins can change this.
            </p>
          )}
        </Card>
      </div>
    </PageContainer>
  );
}
