import type { Role } from "../../lib/permissions";
import { Tag } from "../ui/tag";

const ROLE_VARIANT: Record<Role, "success" | "neutral" | "warning"> = {
  admin: "success",
  user: "neutral",
  viewer: "warning",
};

const ROLE_LABELS: Record<Role, string> = {
  admin: "Admin",
  user: "User",
  viewer: "Viewer",
};

export function RoleBadge({ role }: { role: Role }) {
  return <Tag variant={ROLE_VARIANT[role]}>{ROLE_LABELS[role]}</Tag>;
}
