export type Role = "admin" | "user" | "viewer";

export type Capability =
  | "members.invite"
  | "members.remove"
  | "members.assign_role"
  | "billing.view"
  | "api_keys.manage"
  | "org_settings.manage"
  | "audit.view"
  | "chat.send";

/**
 * Flat role -> capability map. Dify's equivalent (web/utils/permission.ts)
 * resolves capabilities from a per-workspace list of granular permission
 * keys (its newer RBAC layer) because it supports arbitrary named roles.
 * Afridock's plan only needs three fixed roles (E5: Admin/User/Viewer), so a
 * static map is enough — skip that indirection until/unless custom roles
 * are actually needed.
 */
const ROLE_CAPABILITIES: Record<Role, Capability[]> = {
  admin: [
    "members.invite",
    "members.remove",
    "members.assign_role",
    "billing.view",
    "api_keys.manage",
    "org_settings.manage",
    "audit.view",
    "chat.send",
  ],
  user: ["chat.send"],
  viewer: [],
};

export function hasCapability(role: Role, capability: Capability): boolean {
  return ROLE_CAPABILITIES[role].includes(capability);
}
