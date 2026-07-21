import { useQuery } from "@tanstack/react-query";

import { http } from "../lib/api/http";

export type Conversation = {
  id: string;
  title: string;
  preview: string;
  modelProfile: string;
  messageCount: number;
  updatedAt: string;
};

export const conversationsKeys = {
  all: ["conversations"] as const,
  list: (search: string) => [...conversationsKeys.all, "list", search] as const,
};

/**
 * Backs the plan's E4 "Conversation History & Search" scenario — calls
 * `/conversations`, which doesn't exist on the backend yet (same
 * forward-looking-scaffolding status as useChatStream/services/members.ts).
 */
export function useConversations(search: string) {
  return useQuery({
    queryKey: conversationsKeys.list(search),
    queryFn: () =>
      http.get<Conversation[]>(`/conversations${search ? `?q=${encodeURIComponent(search)}` : ""}`),
  });
}
