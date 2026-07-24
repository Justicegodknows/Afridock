import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { http } from "../lib/api/http";

export type CurrentOrganization = {
  id: string;
  name: string;
  allowCommercialFallback: boolean;
};

export const organizationKeys = {
  current: ["organization", "current"] as const,
};

export function useCurrentOrganization() {
  return useQuery({
    queryKey: organizationKeys.current,
    queryFn: () => http.get<CurrentOrganization>("/organizations/current"),
  });
}

export function useUpdateOrganizationSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (allowCommercialFallback: boolean) =>
      http.patch<CurrentOrganization>("/organizations/current/settings", {
        allow_commercial_fallback: allowCommercialFallback,
      }),
    onSuccess: (updated) => queryClient.setQueryData(organizationKeys.current, updated),
  });
}
