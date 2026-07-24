import { type FormEvent, type KeyboardEvent, useState } from "react";

import { Button } from "../ui/button";

type ChatInputProps = {
  disabled: boolean;
  onSubmit: (content: string) => void;
};

export function ChatInput({ disabled, onSubmit }: ChatInputProps) {
  const [value, setValue] = useState("");

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setValue("");
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-divider py-4">
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <textarea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Message Afrikdock…"
          rows={1}
          className="min-h-[52px] max-h-[140px] flex-1 resize-none rounded-md border border-divider bg-bg px-3 py-2.5 text-sm text-text placeholder:text-text-subtle disabled:opacity-50"
        />
        <Button type="submit" variant="primary" disabled={disabled || !value.trim()} className="h-[52px]">
          {disabled ? "Sending…" : "Send"}
        </Button>
      </form>
      <div className="mt-2 flex justify-between text-[11px] text-text-subtle">
        <span>Enter to send · Shift+Enter for a new line</span>
      </div>
    </div>
  );
}
