import { useRevokeApiKey } from "../../services/apiKeys";
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

type RevokeApiKeyAlertDialogProps = {
  keyId: string;
  keyName: string;
};

export function RevokeApiKeyAlertDialog({ keyId, keyName }: RevokeApiKeyAlertDialogProps) {
  const revokeApiKey = useRevokeApiKey();

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <button type="button" className="text-xs text-red-600 hover:text-red-700">
          Revoke
        </button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogTitle>Revoke &quot;{keyName}&quot;?</AlertDialogTitle>
        <AlertDialogDescription>
          Any requests using this key will immediately start returning 401. This can&apos;t be
          undone.
        </AlertDialogDescription>
        <div className="mt-4 flex justify-end gap-2">
          <AlertDialogCancel asChild>
            <Button variant="ghost">Cancel</Button>
          </AlertDialogCancel>
          <AlertDialogAction asChild>
            <button
              type="button"
              onClick={() => revokeApiKey.mutate(keyId)}
              className="inline-flex items-center justify-center rounded-md bg-red-600 px-4 py-2 font-heading text-sm font-semibold text-white hover:bg-red-700"
            >
              Revoke
            </button>
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
