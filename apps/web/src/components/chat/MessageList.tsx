import { useAutoScroll } from "../../hooks/useAutoScroll";
import type { ChatMessage } from "../../store/chatStore";
import { MessageItem } from "./MessageItem";

type MessageListProps = {
  messages: ChatMessage[];
};

export function MessageList({ messages }: MessageListProps) {
  const containerRef = useAutoScroll<HTMLDivElement>(messages);

  return (
    <div ref={containerRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} />
      ))}
    </div>
  );
}
