import { memo } from "react";

import type { ChatMessage } from "../../store/chatStore";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { TypingIndicator } from "./TypingIndicator";

type MessageItemProps = {
  message: ChatMessage;
};

/**
 * Memoized so an in-progress streaming message re-rendering every token
 * doesn't re-render its siblings — mirrors Dify's memo()-wrapped
 * BasicContent/Markdown (web/app/components/base/chat/chat/answer/) plus
 * Zustand+Immer's structural sharing standing in for Dify's Immer-tree state.
 */
export const MessageItem = memo(function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === "user";
  const isEmptyAndStreaming = message.status === "streaming" && message.content === "";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg border px-4 py-3 ${
          isUser ? "border-accent-300 bg-accent-100" : "border-divider bg-surface"
        }`}
      >
        <div
          className={`mb-1.5 text-[10px] uppercase tracking-[0.1em] ${
            isUser ? "text-accent-700" : "text-text-subtle"
          }`}
        >
          {isUser ? "You" : "Assistant"}
        </div>
        {isEmptyAndStreaming ? (
          <TypingIndicator />
        ) : (
          <MarkdownRenderer content={message.content} isStreaming={message.status === "streaming"} />
        )}
        {message.status === "error" && (
          <p className="mt-1 text-xs text-red-600">Something went wrong generating this reply.</p>
        )}
        {!isUser && message.modelProfile && (
          <p className="mt-1 text-xs text-text-subtle">{message.modelProfile}</p>
        )}
      </div>
    </div>
  );
});
