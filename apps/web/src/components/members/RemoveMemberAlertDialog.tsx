import { useRemoveMember } from "../../services/members";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../ui/alert-dialog";
import { Button } from "../ui/button";

type RemoveMemberAlertDialogProps = {
  memberId: string;
  memberLabel: string;
};

export function RemoveMemberAlertDialog({ memberId, memberLabel }: RemoveMemberAlertDialogProps) {
  const removeMember = useRemoveMember();

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <button type="button" className="text-xs text-red-600 hover:text-red-700">
          Remove
        </button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogTitle>Remove {memberLabel}?</AlertDialogTitle>
        <AlertDialogDescription>
          They will immediately lose access to this organization. This can&apos;t be undone.
        </AlertDialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <AlertDialogCancel asChild>
            <Button variant="ghost">Cancel</Button>
          </AlertDialogCancel>
          <AlertDialogAction asChild>
            <button
              type="button"
              onClick={() => removeMember.mutate(memberId)}
              className="inline-flex items-center justify-center rounded-md bg-red-600 px-4 py-2 font-heading text-sm font-semibold text-white hover:bg-red-700"
            >
              Remove
            </button>
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
