import type { ReactNode } from "react";

import { cn } from "../../lib/cn";

type PageContainerProps = {
  children: ReactNode;
  className?: string;
};

/** Owns scrolling + the mockup's centered-column layout for every page
 * except Assistant, which manages its own full-bleed scroll region. */
export function PageContainer({ children, className }: PageContainerProps) {
  return (
    <div className={cn("h-full overflow-y-auto px-8 pb-16 pt-7", className)}>
      <div className="mx-auto max-w-[1000px]">{children}</div>
    </div>
  );
}
