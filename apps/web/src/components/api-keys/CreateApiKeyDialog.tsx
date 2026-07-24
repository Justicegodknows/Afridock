import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useCreateApiKey } from "../../services/apiKeys";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";

const createKeySchema = z.object({
  name: z.string().min(1, "Give this key a name"),
});

type CreateKeyFormValues = z.infer<typeof createKeySchema>;

/**
 * Two-phase dialog: name form, then a one-time reveal of the plaintext key
 * — mirrors InviteMemberDialog's Radix Dialog shape, but the form step is
 * replaced by a copy-once step after creation since the API never returns
 * the plaintext again (see api/routes/api_keys.py).
 */
export function CreateApiKeyDialog() {
  const [open, setOpen] = useState(false);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const createApiKey = useCreateApiKey();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateKeyFormValues>({ resolver: zodResolver(createKeySchema) });

  const onSubmit = handleSubmit(async (values) => {
    const created = await createApiKey.mutateAsync(values.name);
    setCreatedKey(created.key);
  });

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      setCreatedKey(null);
      setCopied(false);
      reset();
    }
  };

  const handleCopy = async () => {
    if (!createdKey) return;
    await navigator.clipboard.writeText(createdKey);
    setCopied(true);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="primary">+ Create API key</Button>
      </DialogTrigger>
      <DialogContent>
        {createdKey ? (
          <>
            <DialogTitle>Copy your API key now</DialogTitle>
            <DialogDescription>
              This is the only time the full key is shown — Afridock only stores its hash.
            </DialogDescription>
            <div className="mt-4 break-all rounded-md border border-divider bg-bg px-3 py-2 font-mono text-xs text-text">
              {createdKey}
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" onClick={handleCopy}>
                {copied ? "Copied" : "Copy"}
              </Button>
              <DialogClose asChild>
                <Button variant="primary">Done</Button>
              </DialogClose>
            </div>
          </>
        ) : (
          <>
            <DialogTitle>Create an API key</DialogTitle>
            <DialogDescription>
              Grants machine access scoped to this organization, at User-level capability.
            </DialogDescription>
            <form onSubmit={onSubmit} className="mt-4 space-y-4">
              <div>
                <label
                  htmlFor="api-key-name"
                  className="mb-1 block text-xs font-medium text-text-muted"
                >
                  Name
                </label>
                <input
                  id="api-key-name"
                  {...register("name")}
                  placeholder="CI integration"
                  className="w-full rounded-md border border-divider bg-bg px-3 py-2 text-sm text-text"
                />
                {errors.name && (
                  <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
                )}
              </div>
              <div className="flex justify-end gap-2">
                <DialogClose asChild>
                  <Button variant="ghost">Cancel</Button>
                </DialogClose>
                <Button type="submit" variant="primary" disabled={isSubmitting}>
                  Create key
                </Button>
              </div>
            </form>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
