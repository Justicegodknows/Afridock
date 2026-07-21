import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { http } from "../lib/api/http";
import type { Role } from "../lib/permissions";

export type Member = {
  id: string;
  email: string;
  name: string | null;
  role: Role;
  status: "active" | "pending";
  lastActiveAt: string | null;
};

/**
 * Query-key factory + hooks, translating Dify's older service-layer pattern
 * (web/service/use-common.ts's commonQueryKeys + useMembers) rather than its
 * newer oRPC-typed client — the oRPC layer solves a scale problem (a huge,
 * fast-moving API surface) Afridock doesn't have yet.
 */
export const membersKeys = {
  all: ["members"] as const,
  list: () => [...membersKeys.all, "list"] as const,
};

export function useMembers() {
  return useQuery({
    queryKey: membersKeys.list(),
    queryFn: () => http.get<Member[]>("/organizations/current/members"),
  });
}

export function useInviteMembers() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { emails: string[]; role: Role }) =>
      http.post<{ invited: string[] }>("/organizations/current/members/invite", input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: membersKeys.list() }),
  });
}

export function useUpdateMemberRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ memberId, role }: { memberId: string; role: Role }) =>
      http.put<Member>(`/organizations/current/members/${memberId}`, { role }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: membersKeys.list() }),
  });
}

export function useRemoveMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (memberId: string) => http.delete<void>(`/organizations/current/members/${memberId}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: membersKeys.list() }),
  });
}
