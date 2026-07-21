import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardKicker } from "../components/ui/card";

type PlaceholderPageProps = {
  phase: string;
  epic: string;
  description: string;
};

/** Shared shell for nav items that exist in the design (full nav shell,
 * per progress.md) but whose real functionality is scoped to a later
 * phase — matches the honest-placeholder pattern already used for
 * Billing/API Keys before this design-unification pass. */
export function PlaceholderPage({ phase, epic, description }: PlaceholderPageProps) {
  return (
    <PageContainer>
      <Card className="max-w-[560px]">
        <CardKicker>{phase}</CardKicker>
        <p className="text-sm text-text-muted">{description}</p>
        <p className="text-xs text-text-subtle">Tracked as {epic} in the execution plan.</p>
      </Card>
    </PageContainer>
  );
}
