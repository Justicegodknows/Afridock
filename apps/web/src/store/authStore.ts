import { create } from "zustand";

import type { Role } from "../lib/permissions";

type AuthState = {
  role: Role;
  setRole: (role: Role) => void;
};

/**
 * Placeholder until Phase 1 E1 (auth & organizations) lands — a real store
 * will populate `role` from a session/JWT instead of this hardcoded default.
 * Kept as its own store now so components depend on `useAuthStore`/
 * `useHasCapability` rather than a hardcoded role, so E1 only has to change
 * this one file.
 */
export const useAuthStore = create<AuthState>((set) => ({
  role: "admin",
  setRole: (role) => set({ role }),
}));
