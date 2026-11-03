import { create } from "zustand";
import { streamChat } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  send: (text: string) => Promise<void>;
  stop: () => void;
  clear: () => void;
}

let controller: AbortController | null = null;
const uid = () => crypto.randomUUID();

export const useChatStore = create<ChatState>((set, get) => {
  const patchLast = (fn: (m: ChatMessage) => ChatMessage) =>
    set((s) => {
      const messages = [...s.messages];
      messages[messages.length - 1] = fn(messages[messages.length - 1]);
      return { messages };
    });

  return {
    messages: [],
    isStreaming: false,

    async send(text) {
      const question = text.trim();
      if (!question || get().isStreaming) return;

      const history = get()
        .messages.filter((m) => m.content && !m.error)
        .map((m) => ({ role: m.role, content: m.content }));

      set((s) => ({
        isStreaming: true,
        messages: [
          ...s.messages,
          { id: uid(), role: "user", content: question },
          { id: uid(), role: "assistant", content: "", streaming: true, steps: [] },
        ],
      }));

      controller = new AbortController();
      try {
        for await (const ev of streamChat([...history, { role: "user", content: question }], controller.signal)) {
          if (ev.event === "route")
            patchLast((m) => ({ ...m, route: ev.data.route, reason: ev.data.reason, searchQuery: ev.data.search_query }));
          else if (ev.event === "step") patchLast((m) => ({ ...m, steps: [...(m.steps ?? []), ev.data] }));
          else if (ev.event === "sources") patchLast((m) => ({ ...m, sources: [...(m.sources ?? []), ...ev.data.sources] }));
          else if (ev.event === "token") patchLast((m) => ({ ...m, content: m.content + ev.data.text }));
          else if (ev.event === "error") patchLast((m) => ({ ...m, error: ev.data.message }));
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError")
          patchLast((m) => ({ ...m, error: (err as Error).message || "Could not reach the server." }));
      } finally {
        patchLast((m) => ({ ...m, streaming: false }));
        set({ isStreaming: false });
        controller = null;
      }
    },

    stop() {
      controller?.abort();
    },

    clear() {
      controller?.abort();
      set({ messages: [], isStreaming: false });
    },
  };
});
