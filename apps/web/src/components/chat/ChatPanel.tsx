import { useEffect, useRef } from "react";

import { useChatStream } from "../../hooks/useChatStream";
import { useConversationMessages } from "../../services/conversations";
import { useChatStore } from "../../store/chatStore";
import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";
import { ModelPicker } from "./ModelPicker";
import { StopButton } from "./StopButton";

type ChatPanelProps = {
  conversationId: string;
};

/**
 * The chat surface (plan E3): a model picker (E2's "model switching at
 * conversation level"), streaming responses, a stop control while
 * generating, and errors surfaced inline on the affected message rather
 * than as a blocking dialog (plan E3's "Error surfaced gracefully" scenario).
 */
export function ChatPanel({ conversationId }: ChatPanelProps) {
  const messages = useChatStore((s) => s.messages);
  const reset = useChatStore((s) => s.reset);
  const addMessage = useChatStore((s) => s.addMessage);
  const { send, stop, isResponding } = useChatStream(conversationId);
  const { data: history } = useConversationMessages(conversationId);

  // Guarded by a ref (not just a `history` dependency) so a background
  // refetch of this query later doesn't wipe out messages already streamed
  // into the store since the initial load (plan E4: "conversations persist
  // across sessions" — this is what makes reopening one show its history).
  const loadedConversationId = useRef<string | null>(null);
  useEffect(() => {
    if (!history || loadedConversationId.current === conversationId) return;
    loadedConversationId.current = conversationId;
    reset();
    for (const message of history) {
      addMessage({
        id: message.id,
        role: message.role,
        content: message.content,
        modelProfile: message.modelProfile ?? undefined,
        status: message.status,
      });
    }
  }, [conversationId, history, reset, addMessage]);

  return (
    <div className="mx-auto flex h-full max-w-[1100px] flex-col px-8">
      <ModelPicker />
      <MessageList messages={messages} />
      <div className="flex items-center justify-end">
        <StopButton isResponding={isResponding} onStop={stop} />
      </div>
      <ChatInput disabled={isResponding} onSubmit={send} />
    </div>
  );
}
