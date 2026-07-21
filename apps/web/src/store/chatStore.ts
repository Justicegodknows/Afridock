import { setAutoFreeze } from "immer";
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";

// Disables Immer's deep-freeze for the lifetime of the app: token-by-token
// streaming updates call `produce` at high frequency, and Dify disables
// autoFreeze for the same reason (web/app/components/base/chat/chat/hooks.ts)
// — structural sharing still works, we just skip the (unneeded) freeze pass.
setAutoFreeze(false);

export type ChatMessageStatus = "streaming" | "complete" | "error";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  modelProfile?: string;
  status: ChatMessageStatus;
};

type ChatState = {
  messages: ChatMessage[];
  isResponding: boolean;
  /** Model for the NEXT message sent — matches plan E2's "model switching at
   * conversation level": already-sent messages keep their own
   * `modelProfile` regardless of later switches (see ChatMessage above). */
  selectedModelProfile: string;
  addMessage: (message: ChatMessage) => void;
  appendToken: (id: string, token: string) => void;
  setStatus: (id: string, status: ChatMessageStatus) => void;
  setModelProfile: (id: string, modelProfile: string) => void;
  setSelectedModelProfile: (modelProfile: string) => void;
  setResponding: (isResponding: boolean) => void;
  reset: () => void;
};

export const useChatStore = create<ChatState>()(
  immer((set) => ({
    messages: [],
    isResponding: false,
    selectedModelProfile: "llama-3.1-8b-instruct",

    addMessage: (message) =>
      set((state) => {
        state.messages.push(message);
      }),

    appendToken: (id, token) =>
      set((state) => {
        const message = state.messages.find((m) => m.id === id);
        if (message) message.content += token;
      }),

    setStatus: (id, status) =>
      set((state) => {
        const message = state.messages.find((m) => m.id === id);
        if (message) message.status = status;
      }),

    setModelProfile: (id, modelProfile) =>
      set((state) => {
        const message = state.messages.find((m) => m.id === id);
        if (message) message.modelProfile = modelProfile;
      }),

    setSelectedModelProfile: (modelProfile) =>
      set((state) => {
        state.selectedModelProfile = modelProfile;
      }),

    setResponding: (isResponding) =>
      set((state) => {
        state.isResponding = isResponding;
      }),

    reset: () =>
      set((state) => {
        state.messages = [];
        state.isResponding = false;
      }),
  })),
);
