import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

export type TagVariant = "neutral" | "success" | "warning";

const VARIANT_CLASSES: Record<TagVariant, string> = {
  neutral: "bg-neutral-200 text-neutral-700",
  success: "bg-accent-100 text-accent-700",
  warning: "bg-accent-200 text-accent-800",
};

type TagProps = {
  variant?: TagVariant;
  children: ReactNode;
  className?: string;
};

export function Tag({ variant = "neutral", children, className }: TagProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm px-2.5 py-0.5 text-[11px] tracking-wide",
        VARIANT_CLASSES[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
