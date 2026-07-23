import { useEffect } from "react";

import { fetchCurrentUser } from "../services/auth";
import { useAuthStore } from "../store/authStore";

/**
 * Resolves the real session once per app load (GET /users/me, cookie-based
 * — see services/auth.ts) instead of trusting a hardcoded role. Runs only
 * while status is "loading" so it doesn't re-fire on every render or after
 * an explicit logout.
 */
export function useAuthBootstrap(): void {
  const status = useAuthStore((s) => s.status);
  const setUser = useAuthStore((s) => s.setUser);
  const clear = useAuthStore((s) => s.clear);

  useEffect(() => {
    if (status !== "loading") return;
    let cancelled = false;
    fetchCurrentUser()
      .then((user) => {
        if (!cancelled) setUser(user);
      })
      .catch(() => {
        if (!cancelled) clear();
      });
    return () => {
      cancelled = true;
    };
  }, [status, setUser, clear]);
}
