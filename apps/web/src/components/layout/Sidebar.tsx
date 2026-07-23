import { NavLink } from "react-router-dom";

import { useTheme } from "../../hooks/useTheme";
import { logout } from "../../services/auth";
import { useAuthStore } from "../../store/authStore";
import { WorkspaceSwitcher } from "../members/WorkspaceSwitcher";
import { ApiStatusIndicator } from "./ApiStatusIndicator";

type NavItem = {
  to: string;
  label: string;
  icon: string;
};

type NavSection = {
  heading: string;
  items: NavItem[];
};

/**
 * Full nav shell matching the AfricaAI Platform design mockup — all 10
 * items exist now even though most route to phase-gated placeholders (see
 * routes/*Page.tsx); only Assistant, Conversations, and Team & Roles have
 * real functionality behind them today. "Projects" (not in the plan's
 * epics) is deferred to Phase 4 — see progress.md and the plan's Phase 4
 * epic list.
 */
const NAV_SECTIONS: NavSection[] = [
  {
    heading: "Workspace",
    items: [
      { to: "/chat", label: "Assistant", icon: "chat" },
      { to: "/conversations", label: "Conversations", icon: "history" },
      { to: "/projects", label: "Projects", icon: "projects" },
    ],
  },
  {
    heading: "Automation",
    items: [{ to: "/workflows", label: "Workflows", icon: "workflows" }],
  },
  {
    heading: "Insights",
    items: [
      { to: "/usage", label: "Usage & Cost", icon: "usage" },
      { to: "/audit", label: "Audit Log", icon: "audit" },
    ],
  },
  {
    heading: "Administration",
    items: [
      { to: "/team", label: "Team & Roles", icon: "team" },
      { to: "/integrations", label: "Integrations", icon: "integrations" },
      { to: "/billing", label: "Billing", icon: "billing" },
      { to: "/resilience", label: "Resilience", icon: "resilience" },
    ],
  },
];

const DEMO_WORKSPACES = [{ id: "demo", name: "Afridock Demo Org" }];

export function Sidebar() {
  const role = useAuthStore((state) => state.role);
  const user = useAuthStore((state) => state.user);
  const clear = useAuthStore((state) => state.clear);
  const { theme, toggleTheme } = useTheme();

  const initials = user?.email?.slice(0, 2).toUpperCase() ?? "?";

  const handleLogout = () => {
    logout()
      .catch(() => {
        /* cookie may already be gone (e.g. it expired) — clear local state regardless */
      })
      .finally(() => {
        clear();
        window.location.href = "/login";
      });
  };

  return (
    <aside className="flex h-full flex-col overflow-hidden border-r border-divider bg-surface">
      <div className="border-b border-divider px-5 pb-4 pt-5">
        <div className="flex items-center gap-2.5">
          <div className="grid h-[30px] w-[30px] place-items-center rounded-sm border border-accent font-heading text-lg font-semibold text-accent">
            A
          </div>
          <div>
            <div className="font-heading text-[19px] font-semibold leading-none">Afridock</div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-accent">
              Enterprise Platform
            </div>
          </div>
        </div>
        <div className="mt-3">
          <WorkspaceSwitcher
            workspaces={DEMO_WORKSPACES}
            currentWorkspaceId="demo"
            onChange={() => {
              /* single demo workspace until E1 lands */
            }}
          />
        </div>
      </div>

      <nav className="flex-1 overflow-auto py-3.5">
        {NAV_SECTIONS.map((section) => (
          <div key={section.heading}>
            <h6 className="mb-1 mt-4 px-5 text-[11px] font-semibold uppercase tracking-wide text-text-subtle first:mt-1.5">
              {section.heading}
            </h6>
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 border-l-2 px-[18px] py-2 text-sm transition-colors hover:bg-hover-overlay ${
                    isActive
                      ? "border-accent text-accent"
                      : "border-transparent text-text-muted"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="flex items-center gap-2.5 border-t border-divider px-5 py-3.5">
        <div className="grid h-7 w-7 flex-none place-items-center rounded-full border border-divider font-heading text-xs text-accent">
          {initials}
        </div>
        <div className="min-w-0 flex-1">
          <div className="truncate font-heading text-[13px] font-semibold leading-none">
            {user?.email ?? "…"}
          </div>
          <div className="text-[11px] capitalize text-text-subtle">{role}</div>
        </div>
        <button
          type="button"
          onClick={toggleTheme}
          aria-label="Toggle color theme"
          className="rounded-md border border-divider px-2 py-1 text-[11px] text-text-muted hover:text-text"
        >
          {theme === "dark" ? "Light" : "Dark"}
        </button>
        <button
          type="button"
          onClick={handleLogout}
          aria-label="Log out"
          className="rounded-md border border-divider px-2 py-1 text-[11px] text-text-muted hover:text-text"
        >
          Log out
        </button>
      </div>
      <div className="border-t border-divider px-5 py-2">
        <ApiStatusIndicator />
      </div>
    </aside>
  );
}
