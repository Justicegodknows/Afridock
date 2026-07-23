import { create } from "zustand";

import type { CurrentUser } from "../services/auth";
import type { Role } from "../lib/permissions";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

type AuthState = {
  status: AuthStatus;
  user: CurrentUser | null;
  /** Mirrors `user.role` — kept as a top-level field since Sidebar and
   * useHasCapability already read `state.role` directly (E1 only needed to
   * change how this store is populated, not every consumer). */
  role: Role;
  setUser: (user: CurrentUser) => void;
  clear: () => void;
};

/**
 * Populated from a real session (see hooks/useAuthBootstrap.ts, which calls
 * GET /users/me on app load) instead of E1's hardcoded `"admin"` placeholder.
 */
export const useAuthStore = create<AuthState>((set) => ({
  status: "loading",
  user: null,
  role: "viewer",
  setUser: (user) => set({ user, role: user.role, status: "authenticated" }),
  clear: () => set({ user: null, role: "viewer", status: "unauthenticated" }),
}));
