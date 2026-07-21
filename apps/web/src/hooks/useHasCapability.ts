import { type Capability, hasCapability } from "../lib/permissions";
import { useAuthStore } from "../store/authStore";

export function useHasCapability(capability: Capability): boolean {
  const role = useAuthStore((state) => state.role);
  return hasCapability(role, capability);
}
