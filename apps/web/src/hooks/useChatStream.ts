import { useCallback, useRef } from "react";

import { streamRequest } from "../lib/api/http";
import { parseSSEStream } from "../lib/sse";
import { useChatStore } from "../store/chatStore";

let messageCounter = 0;
function nextId(prefix: string): string {
  messageCounter += 1;
  return `${prefix}-${messageCounter}`;
}

/**
 * Owns one in-flight streaming request at a time for a conversation: sends
 * the user's message, streams the assistant's reply token-by-token into
 * chatStore, and exposes `stop()` to abort — the same shape as Dify's
 * `useChat` (web/app/components/base/chat/chat/hooks.ts), reimplemented for
 * native fetch/SSE + Zustand instead of Dify's ssePost + component state.
 *
 * POSTs to `/conversations/:id/messages`, the endpoint E2/E3 (Phase 1) will
 * implement — this hook is forward-looking scaffolding, same as the
 * /healthz-only API skeleton it currently talks to nothing else on.
 */
export function useChatStream(conversationId: string) {
  const abortRef = useRef<AbortController | null>(null);

  const addMessage = useChatStore((s) => s.addMessage);
  const appendToken = useChatStore((s) => s.appendToken);
  const setStatus = useChatStore((s) => s.setStatus);
  const setModelProfile = useChatStore((s) => s.setModelProfile);
  const setResponding = useChatStore((s) => s.setResponding);
  const isResponding = useChatStore((s) => s.isResponding);
  const selectedModelProfile = useChatStore((s) => s.selectedModelProfile);

  const send = useCallback(
    async (content: string) => {
      addMessage({ id: nextId("user"), role: "user", content, status: "complete" });

      const assistantMessageId = nextId("assistant");
      addMessage({
        id: assistantMessageId,
        role: "assistant",
        content: "",
        status: "streaming",
        modelProfile: selectedModelProfile,
      });
      setResponding(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await streamRequest(
          `/conversations/${conversationId}/messages`,
          { content, model_profile: selectedModelProfile },
          controller.signal,
        );

        if (!response.ok) {
          throw new Error(`chat request failed: ${response.status}`);
        }

        await parseSSEStream(
          response,
          {
            onEvent: ({ event, data }) => {
              if (event === "message" && typeof data.delta === "string") {
                appendToken(assistantMessageId, data.delta);
              } else if (event === "message_end") {
                if (typeof data.model_profile === "string") {
                  setModelProfile(assistantMessageId, data.model_profile);
                }
                setStatus(assistantMessageId, "complete");
              } else if (event === "error") {
                setStatus(assistantMessageId, "error");
              }
            },
          },
          controller.signal,
        );
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) {
          setStatus(assistantMessageId, "error");
        }
      } finally {
        setResponding(false);
        abortRef.current = null;
      }
    },
    [
      conversationId,
      addMessage,
      appendToken,
      setStatus,
      setModelProfile,
      setResponding,
      selectedModelProfile,
    ],
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { send, stop, isResponding };
}
