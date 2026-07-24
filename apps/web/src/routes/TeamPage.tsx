import { type ReactNode, useState } from "react";

import { ApiKeysTable } from "../components/api-keys/ApiKeysTable";
import { CreateApiKeyDialog } from "../components/api-keys/CreateApiKeyDialog";
import { PageContainer } from "../components/layout/PageContainer";
import { InviteMemberDialog } from "../components/members/InviteMemberDialog";
import { MembersTable } from "../components/members/MembersTable";
import { Card, CardBody, CardKicker } from "../components/ui/card";
import { useHasCapability } from "../hooks/useHasCapability";
import { useApiKeys } from "../services/apiKeys";
import { useMembers } from "../services/members";

const ROLE_CARDS = [
  { kicker: "Admin", body: "Full control: billing, members, integrations, audit access." },
  { kicker: "User", body: "Chat with all models, manage own conversations & keys." },
  { kicker: "Viewer", body: "Read-only access to shared conversations and reports." },
];

type Tab = "members" | "api-keys";

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`-mb-px border-b-2 pb-2 text-sm ${
        active ? "border-accent text-accent" : "border-transparent text-text-muted"
      }`}
    >
      {children}
    </button>
  );
}

function ApiKeysSection() {
  const { data: apiKeys, isLoading, isError } = useApiKeys();
  const canManage = useHasCapability("api_keys.manage");

  if (!canManage) {
    return (
      <p className="text-sm text-text-muted">Only Admins can view and manage API keys.</p>
    );
  }

  return (
    <>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-heading text-xl">
          API keys{apiKeys ? ` · ${apiKeys.length}` : ""}
        </h3>
        <CreateApiKeyDialog />
      </div>
      {isLoading && <p className="text-sm text-text-muted">Loading API keys…</p>}
      {isError && <p className="text-sm text-red-600">Couldn&apos;t load API keys.</p>}
      {apiKeys && apiKeys.length > 0 && <ApiKeysTable apiKeys={apiKeys} />}
      {apiKeys && apiKeys.length === 0 && (
        <p className="text-sm text-text-muted">No API keys yet.</p>
      )}
    </>
  );
}

/**
 * "Team & Roles" — the mockup's flat screen (role-explainer cards + a
 * members table with an inline role select), moved to a top-level route
 * instead of nesting under a settings sub-nav (the AppShell sidebar already
 * plays that role). API Keys, which the mockup doesn't have its own nav
 * item for but the plan's E5 requires, lives as a tab here instead of a
 * standalone nav entry.
 */
export function TeamPage() {
  const [tab, setTab] = useState<Tab>("members");
  const { data: members, isLoading, isError } = useMembers();
  const canInvite = useHasCapability("members.invite");

  return (
    <PageContainer>
      <div className="mb-6 flex gap-3.5">
        {ROLE_CARDS.map((card) => (
          <Card key={card.kicker} className="flex-1">
            <CardKicker>{card.kicker}</CardKicker>
            <CardBody>{card.body}</CardBody>
          </Card>
        ))}
      </div>

      <div className="mb-4 flex items-center gap-5 border-b border-divider">
        <TabButton active={tab === "members"} onClick={() => setTab("members")}>
          Members
        </TabButton>
        <TabButton active={tab === "api-keys"} onClick={() => setTab("api-keys")}>
          API Keys
        </TabButton>
      </div>

      {tab === "members" ? (
        <>
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-heading text-xl">Members{members ? ` · ${members.length}` : ""}</h3>
            {canInvite && <InviteMemberDialog />}
          </div>
          {isLoading && <p className="text-sm text-text-muted">Loading members…</p>}
          {isError && <p className="text-sm text-red-600">Couldn&apos;t load members.</p>}
          {members && members.length > 0 && <MembersTable members={members} />}
          {members && members.length === 0 && (
            <p className="text-sm text-text-muted">No members yet.</p>
          )}
        </>
      ) : (
        <ApiKeysSection />
      )}
    </PageContainer>
  );
}
