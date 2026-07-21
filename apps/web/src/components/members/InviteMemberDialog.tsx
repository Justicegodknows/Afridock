import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { Role } from "../../lib/permissions";
import { useInviteMembers } from "../../services/members";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";

const inviteSchema = z.object({
  emails: z.string().min(1, "Enter at least one email"),
  role: z.enum(["admin", "user", "viewer"]),
});

type InviteFormValues = z.infer<typeof inviteSchema>;

/**
 * Multi-email + role invite, mirroring the shape of Dify's invite-modal
 * (web/app/components/header/account-setting/members-page/invite-modal/) —
 * a comma/whitespace-separated text field stands in for Dify's chip-style
 * email input, which is a UX nicety not core to the pattern being adapted.
 */
export function InviteMemberDialog() {
  const [open, setOpen] = useState(false);
  const inviteMembers = useInviteMembers();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<InviteFormValues>({
    resolver: zodResolver(inviteSchema),
    defaultValues: { emails: "", role: "user" },
  });

  const onSubmit = handleSubmit(async (values) => {
    const emails = values.emails
      .split(/[,\s]+/)
      .map((email) => email.trim())
      .filter(Boolean);
    await inviteMembers.mutateAsync({ emails, role: values.role as Role });
    reset();
    setOpen(false);
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="primary">+ Invite member</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>Invite members</DialogTitle>
        <DialogDescription>Send an email invite with an assigned role.</DialogDescription>
        <form onSubmit={onSubmit} className="mt-4 space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">Emails</label>
            <textarea
              {...register("emails")}
              rows={3}
              placeholder="ada@example.com, grace@example.com"
              className="w-full rounded-md border border-divider bg-bg px-3 py-2 text-sm text-text"
            />
            {errors.emails && <p className="mt-1 text-xs text-red-600">{errors.emails.message}</p>}
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-text-muted">Role</label>
            <select
              {...register("role")}
              className="w-full rounded-md border border-divider bg-bg px-3 py-2 text-sm text-text"
            >
              <option value="admin">Admin</option>
              <option value="user">User</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <DialogClose asChild>
              <Button variant="ghost">Cancel</Button>
            </DialogClose>
            <Button type="submit" variant="primary" disabled={isSubmitting}>
              Send invites
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
