import { beforeEach, describe, expect, it } from "vitest";

import { useChatStore } from "../src/store/chatStore";

describe("chatStore", () => {
  beforeEach(() => {
    useChatStore.getState().reset();
  });

  it("appends tokens to the target message without touching others", () => {
    const { addMessage, appendToken } = useChatStore.getState();

    addMessage({ id: "a", role: "assistant", content: "", status: "streaming" });
    addMessage({ id: "b", role: "assistant", content: "unchanged", status: "complete" });

    appendToken("a", "Hel");
    appendToken("a", "lo");

    const { messages } = useChatStore.getState();
    expect(messages.find((m) => m.id === "a")?.content).toBe("Hello");
    expect(messages.find((m) => m.id === "b")?.content).toBe("unchanged");
  });

  it("tracks per-message status and model attribution independently", () => {
    const { addMessage, setStatus, setModelProfile } = useChatStore.getState();

    addMessage({ id: "a", role: "assistant", content: "hi", status: "streaming" });
    setStatus("a", "complete");
    setModelProfile("a", "llama-3.1-8b-instruct");

    const message = useChatStore.getState().messages.find((m) => m.id === "a");
    expect(message?.status).toBe("complete");
    expect(message?.modelProfile).toBe("llama-3.1-8b-instruct");
  });
});
