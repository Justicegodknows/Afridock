import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { http } from "../lib/api/http";

export type ApiKey = {
  id: string;
  name: string;
  keyPrefix: string;
  createdAt: string;
  lastUsedAt: string | null;
  revokedAt: string | null;
};

export type CreatedApiKey = ApiKey & { key: string };

export const apiKeysKeys = {
  all: ["api-keys"] as const,
  list: () => [...apiKeysKeys.all, "list"] as const,
};

export function useApiKeys() {
  return useQuery({
    queryKey: apiKeysKeys.list(),
    queryFn: () => http.get<ApiKey[]>("/organizations/current/api-keys"),
  });
}

export function useCreateApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      http.post<CreatedApiKey>("/organizations/current/api-keys", { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: apiKeysKeys.list() }),
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (keyId: string) => http.delete<void>(`/organizations/current/api-keys/${keyId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: apiKeysKeys.list() }),
  });
}
