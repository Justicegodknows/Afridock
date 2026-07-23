import { useMutation, useQuery } from "@tanstack/react-query";

import { http } from "../lib/api/http";

export type Conversation = {
  id: string;
  title: string;
  preview: string;
  modelProfile: string;
  messageCount: number;
  updatedAt: string;
};

export type ConversationMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  modelProfile: string | null;
  status: "complete" | "error";
};

export const conversationsKeys = {
  all: ["conversations"] as const,
  list: (search: string) => [...conversationsKeys.all, "list", search] as const,
  messages: (conversationId: string) => [...conversationsKeys.all, conversationId, "messages"] as const,
};

/** Backs the plan's E4 "Conversation History & Search" scenario. */
export function useConversations(search: string) {
  return useQuery({
    queryKey: conversationsKeys.list(search),
    queryFn: () =>
      http.get<Conversation[]>(`/conversations${search ? `?q=${encodeURIComponent(search)}` : ""}`),
  });
}

/** Loads persisted history for ChatPanel on mount when resuming a conversation. */
export function useConversationMessages(conversationId: string | undefined) {
  return useQuery({
    queryKey: conversationsKeys.messages(conversationId ?? ""),
    queryFn: () => http.get<ConversationMessage[]>(`/conversations/${conversationId}/messages`),
    enabled: Boolean(conversationId),
  });
}

/** Bare `/chat` creates a conversation and redirects to `/chat/:id` — see routes/ChatPage.tsx. */
export function useCreateConversation() {
  return useMutation({
    mutationFn: (modelProfile?: string) =>
      http.post<{ id: string }>("/conversations", { model_profile: modelProfile }),
  });
}
