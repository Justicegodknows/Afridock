import { useState } from "react";
import { Link } from "react-router-dom";

import { PageContainer } from "../components/layout/PageContainer";
import { Tag } from "../components/ui/tag";
import { useConversations } from "../services/conversations";

export function ConversationsPage() {
  const [search, setSearch] = useState("");
  const { data: conversations, isLoading, isError } = useConversations(search);

  return (
    <PageContainer>
      <div className="mb-5 flex items-center gap-3">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search conversations, models, topics…"
          className="flex-1 rounded-md border border-divider bg-bg px-3 py-2 text-sm text-text placeholder:text-text-subtle"
        />
        <span className="whitespace-nowrap text-xs text-text-subtle">
          {conversations?.length ?? 0} conversations
        </span>
      </div>

      {isLoading && <p className="text-sm text-text-muted">Loading conversations…</p>}
      {isError && <p className="text-sm text-red-600">Couldn&apos;t load conversations.</p>}
      {conversations && conversations.length === 0 && (
        <p className="text-sm text-text-muted">
          No conversations yet — start one from{" "}
          <Link to="/chat" className="text-accent underline">
            Assistant
          </Link>
          .
        </p>
      )}

      <div className="flex flex-col divide-y divide-divider">
        {conversations?.map((conversation) => (
          <Link
            key={conversation.id}
            to="/chat"
            className="flex items-center justify-between gap-4 py-3 hover:bg-hover-overlay"
          >
            <div className="min-w-0">
              <div className="font-heading text-[15px]">{conversation.title}</div>
              <div className="truncate text-xs text-text-muted">{conversation.preview}</div>
            </div>
            <div className="flex flex-none items-center gap-3">
              <Tag variant="neutral">{conversation.modelProfile}</Tag>
              <span className="text-xs text-text-subtle">{conversation.updatedAt}</span>
            </div>
          </Link>
        ))}
      </div>
    </PageContainer>
  );
}
