import { useChatStream } from "../../hooks/useChatStream";
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
  const { send, stop, isResponding } = useChatStream(conversationId);

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
