import { useHasCapability } from "../../hooks/useHasCapability";
import type { Role } from "../../lib/permissions";
import type { Member } from "../../services/members";
import { useUpdateMemberRole } from "../../services/members";
import { RemoveMemberAlertDialog } from "./RemoveMemberAlertDialog";
import { RoleBadge } from "./RoleBadge";

const ROLE_OPTIONS: Role[] = ["admin", "user", "viewer"];

type MembersTableProps = {
  members: Member[];
};

function initialsOf(label: string): string {
  return label
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

/**
 * Plain mapped rows, no virtualization/pagination — same scale assumption
 * Dify's MembersPage makes (web/app/components/header/account-setting/
 * members-page/index.tsx), reasonable until an org has hundreds of members.
 */
export function MembersTable({ members }: MembersTableProps) {
  const canAssignRole = useHasCapability("members.assign_role");
  const canRemove = useHasCapability("members.remove");
  const updateRole = useUpdateMemberRole();

  return (
    <table className="w-full text-left text-sm">
      <thead className="text-text-subtle">
        <tr>
          <th className="pb-2 font-medium">Member</th>
          <th className="pb-2 font-medium">Email</th>
          <th className="pb-2 font-medium">Role</th>
          <th className="pb-2 font-medium">Status</th>
          {canRemove && <th className="pb-2 font-medium" />}
        </tr>
      </thead>
      <tbody className="divide-y divide-divider">
        {members.map((member) => {
          const label = member.name ?? member.email;
          return (
            <tr key={member.id}>
              <td className="flex items-center gap-2.5 py-2.5">
                <span className="grid h-7 w-7 place-items-center rounded-full border border-divider font-heading text-xs text-accent">
                  {initialsOf(label)}
                </span>
                <span className="font-heading text-[15px]">{label}</span>
              </td>
              <td className="py-2.5 text-text-muted">{member.email}</td>
              <td className="py-2.5">
                {canAssignRole ? (
                  <select
                    value={member.role}
                    onChange={(event) =>
                      updateRole.mutate({ memberId: member.id, role: event.target.value as Role })
                    }
                    className="rounded-md border border-divider bg-bg px-2 py-1 text-xs text-text"
                  >
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                ) : (
                  <RoleBadge role={member.role} />
                )}
              </td>
              <td className="py-2.5 text-xs text-text-muted">
                {member.status === "pending" ? "Pending invite" : "Active"}
              </td>
              {canRemove && (
                <td className="py-2.5 text-right">
                  <RemoveMemberAlertDialog memberId={member.id} memberLabel={label} />
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
