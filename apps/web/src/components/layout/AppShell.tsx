import { Outlet, useLocation } from "react-router-dom";

import { PageHeader } from "./PageHeader";
import { Sidebar } from "./Sidebar";

type PageMeta = { match: (pathname: string) => boolean; kicker: string; title: string };

const PAGE_META: PageMeta[] = [
  { match: (p) => p === "/" || p.startsWith("/chat"), kicker: "Workspace", title: "Assistant" },
  { match: (p) => p.startsWith("/conversations"), kicker: "Workspace", title: "Conversations" },
  { match: (p) => p.startsWith("/projects"), kicker: "Workspace", title: "Projects" },
  { match: (p) => p.startsWith("/workflows"), kicker: "Automation", title: "Workflows" },
  { match: (p) => p.startsWith("/usage"), kicker: "Insights", title: "Usage & Cost" },
  { match: (p) => p.startsWith("/audit"), kicker: "Insights", title: "Audit Log" },
  { match: (p) => p.startsWith("/team"), kicker: "Administration", title: "Team & Roles" },
  { match: (p) => p.startsWith("/integrations"), kicker: "Administration", title: "Integrations" },
  { match: (p) => p.startsWith("/billing"), kicker: "Administration", title: "Billing" },
  { match: (p) => p.startsWith("/resilience"), kicker: "Administration", title: "Resilience" },
  { match: (p) => p.startsWith("/workspace"), kicker: "Workspace", title: "Workspace settings" },
];

function resolvePageMeta(pathname: string): { kicker: string; title: string } {
  const entry = PAGE_META.find((candidate) => candidate.match(pathname));
  return entry ? { kicker: entry.kicker, title: entry.title } : { kicker: "Afridock", title: "" };
}

/**
 * Single-sidebar app shell replacing the old per-section SettingsLayout —
 * matches the design mockup's one-sidebar structure rather than nesting a
 * second sidebar inside a settings area. `<main>` is overflow-hidden; each
 * page owns its own scroll container (PageContainer for simple pages,
 * ChatPanel's internal MessageList scroll region for the Assistant screen).
 */
export function AppShell() {
  const location = useLocation();
  const { kicker, title } = resolvePageMeta(location.pathname);

  return (
    <div className="grid h-screen grid-cols-[250px_1fr] overflow-hidden bg-bg text-text">
      <Sidebar />
      <div className="flex min-w-0 flex-col overflow-hidden">
        <header className="flex items-center gap-4 border-b border-divider px-[30px] py-3.5">
          <PageHeader kicker={kicker} title={title} />
        </header>
        <main className="flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
