import { useEffect } from "react";

import { useAuthBootstrap } from "../../hooks/useAuthBootstrap";
import { useAuthStore } from "../../store/authStore";

type AuthGuardProps = {
  children: React.ReactNode;
};

/**
 * Gates the protected route tree behind a real session. Redirects with
 * `window.location.href` (a hard navigation), not React Router's
 * `<Navigate>`/loader redirects — those construct a `Request`/`AbortSignal`
 * internally, which crashes under vitest+jsdom (a jsdom/undici realm
 * mismatch worked around elsewhere in this router by avoiding client-side
 * navigation on mount entirely); a plain browser redirect sidesteps that
 * class of bug altogether and is simpler for an auth boundary regardless.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  useAuthBootstrap();
  const status = useAuthStore((s) => s.status);

  useEffect(() => {
    if (status === "unauthenticated") {
      window.location.href = "/login";
    }
  }, [status]);

  if (status !== "authenticated") {
    return null;
  }

  return <>{children}</>;
}
