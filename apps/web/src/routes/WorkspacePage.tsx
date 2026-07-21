import { PageContainer } from "../components/layout/PageContainer";
import { Card, CardBody, CardKicker } from "../components/ui/card";

/**
 * Reachable from the sidebar's WorkspaceSwitcher (⚙ link), not the primary
 * nav — the mockup has no dedicated "Organization" nav item, only a
 * workspace-create dialog, so profile editing for the *current* workspace
 * lives here instead of competing for a spot among the mockup's 10 items.
 */
export function WorkspacePage() {
  return (
    <PageContainer>
      <Card className="max-w-[560px]">
        <CardKicker>Phase 1 · E1</CardKicker>
        <CardBody>
          Workspace profile, name, and tenant settings land here with Phase 1 E1 (auth &amp;
          organizations).
        </CardBody>
      </Card>
    </PageContainer>
  );
}
