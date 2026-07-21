import { type ComponentProps, forwardRef } from "react";

import { cn } from "../../lib/cn";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-accent text-white hover:bg-accent-600",
  secondary: "border border-divider text-text hover:bg-hover-overlay",
  ghost: "text-text-muted hover:text-text",
  danger: "text-red-600 hover:text-red-700",
};

type ButtonProps = ComponentProps<"button"> & {
  variant?: ButtonVariant;
};

// forwardRef is required, not stylistic: Radix's `asChild`/Slot pattern
// (DialogTrigger asChild, AlertDialogCancel asChild, etc.) clones this
// component and attaches its own ref to the underlying DOM node for focus
// management — a plain function component can't receive that ref, and
// React logs "Function components cannot be given refs" whenever this
// button is used inside one of those triggers.
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "secondary", className, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center gap-1.5 rounded-md px-4 py-2 font-heading text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        VARIANT_CLASSES[variant],
        className,
      )}
      {...props}
    />
  );
});
