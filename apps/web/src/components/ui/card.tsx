import type { ComponentProps, ReactNode } from "react";

import { cn } from "../../lib/cn";

export function Card({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-md border border-divider bg-surface p-4 shadow-sm",
        className,
      )}
      {...props}
    />
  );
}

export function CardKicker({ children }: { children: ReactNode }) {
  return <div className="text-[11px] uppercase tracking-wider text-accent">{children}</div>;
}

export function CardTitle({ children }: { children: ReactNode }) {
  return <div className="font-heading text-lg font-semibold">{children}</div>;
}

export function CardBody({ children }: { children: ReactNode }) {
  return <p className="text-sm text-text-muted">{children}</p>;
}

export function CardMeta({ children }: { children: ReactNode }) {
  return <div className="text-xs text-text-subtle">{children}</div>;
}
