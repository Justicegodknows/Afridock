import { Link } from "react-router-dom";

type Workspace = {
  id: string;
  name: string;
};

type WorkspaceSwitcherProps = {
  workspaces: Workspace[];
  currentWorkspaceId: string;
  onChange: (workspaceId: string) => void;
};

/**
 * Presentational only — org data/switching lands with Phase 1 E1. Mirrors
 * Dify's workplace-selector (web/app/components/header/account-dropdown/
 * workplace-selector/), simplified from a custom dropdown to a native
 * select since Afridock doesn't need per-item avatar/plan-badge composition
 * yet. The mockup has no dedicated "Organization" nav item — workspace
 * profile editing is reachable from here instead, via the link below.
 */
export function WorkspaceSwitcher({ workspaces, currentWorkspaceId, onChange }: WorkspaceSwitcherProps) {
  return (
    <div className="flex items-center gap-1.5">
      <select
        value={currentWorkspaceId}
        onChange={(event) => onChange(event.target.value)}
        className="min-w-0 flex-1 rounded-md border border-divider bg-bg px-2 py-1 text-xs text-text"
      >
        {workspaces.map((workspace) => (
          <option key={workspace.id} value={workspace.id}>
            {workspace.name}
          </option>
        ))}
      </select>
      <Link
        to="/workspace"
        title="Workspace settings"
        className="rounded-md border border-divider px-1.5 py-1 text-xs text-text-subtle hover:text-text"
      >
        ⚙
      </Link>
    </div>
  );
}
