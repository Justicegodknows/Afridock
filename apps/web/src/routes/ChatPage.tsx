import { useEffect } from "react";
import { useParams } from "react-router-dom";

import { ChatPanel } from "../components/chat/ChatPanel";
import { useCreateConversation } from "../services/conversations";

/**
 * Bare `/chat` has no conversation yet — it creates one and hard-redirects
 * to `/chat/:conversationId` (not `useNavigate`/`<Navigate>`: this router
 * already works around a jsdom/AbortSignal crash from React Router's
 * internal Request construction by avoiding client-side navigation on
 * mount entirely — see router.tsx and AuthGuard.tsx for the same pattern).
 */
function NewChatRedirect() {
  const createConversation = useCreateConversation();

  useEffect(() => {
    if (createConversation.status !== "idle") return;
    createConversation.mutate(undefined, {
      onSuccess: (conversation) => {
        window.location.href = `/chat/${conversation.id}`;
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
}

export function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>();

  if (!conversationId) {
    return <NewChatRedirect />;
  }

  return <ChatPanel conversationId={conversationId} />;
}
