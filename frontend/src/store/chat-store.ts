import { create } from "zustand";
import { streamChat, streamChatResume } from "@/lib/api";
import type { ChatMessage, StreamEvent, WebSearchInterrupt } from "@/lib/types";

interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  pendingInterrupt: WebSearchInterrupt | null;
  activeThreadId: string | null;
  send: (text: string) => Promise<void>;
  resolveInterrupt: (decision: "YES" | "NO") => Promise<void>;
  stop: () => void;
  clear: () => void;
}

let controller: AbortController | null = null;
const uid = () => crypto.randomUUID();

/** Batch token updates to one React commit per animation frame — cuts markdown flicker. */
function createTokenBatcher(flush: (chunk: string) => void) {
  let pending = "";
  let raf = 0;

  return {
    push(text: string) {
      pending += text;
      if (raf) return;
      raf = requestAnimationFrame(() => {
        const chunk = pending;
        pending = "";
        raf = 0;
        if (chunk) flush(chunk);
      });
    },
    flushNow() {
      if (raf) {
        cancelAnimationFrame(raf);
        raf = 0;
      }
      if (pending) {
        const chunk = pending;
        pending = "";
        flush(chunk);
      }
    },
  };
}

export const useChatStore = create<ChatState>((set, get) => {
  const patchLast = (fn: (m: ChatMessage) => ChatMessage) =>
    set((s) => {
      const messages = [...s.messages];
      messages[messages.length - 1] = fn(messages[messages.length - 1]);
      return { messages };
    });

  const applyStreamEvent = (
    ev: StreamEvent,
    tokens: ReturnType<typeof createTokenBatcher>,
  ): "interrupt" | "continue" => {
    if (ev.event === "route") {
      if (ev.data.thread_id) set({ activeThreadId: ev.data.thread_id });
      patchLast((m) => ({
        ...m,
        route: ev.data.route,
        reason: ev.data.reason,
        searchQuery: ev.data.search_query,
      }));
    } else if (ev.event === "step") {
      patchLast((m) => ({ ...m, steps: [...(m.steps ?? []), ev.data] }));
    } else if (ev.event === "sources") {
      patchLast((m) => ({ ...m, sources: [...(m.sources ?? []), ...ev.data.sources] }));
    } else if (ev.event === "token") {
      tokens.push(ev.data.text);
    } else if (ev.event === "error") {
      patchLast((m) => ({ ...m, error: ev.data.message }));
    } else if (ev.event === "interrupt") {
      tokens.flushNow();
      set({
        pendingInterrupt: {
          thread_id: ev.data.thread_id,
          type: ev.data.type,
          message: ev.data.message,
          search_query: ev.data.search_query,
          reason: ev.data.reason,
          route: ev.data.route,
        },
        activeThreadId: ev.data.thread_id,
        isStreaming: false,
      });
      patchLast((m) => ({ ...m, streaming: false, awaitingApproval: true }));
      return "interrupt";
    } else if (ev.event === "done" && ev.data.thread_id) {
      set({ activeThreadId: ev.data.thread_id });
    }
    return "continue";
  };

  return {
    messages: [],
    isStreaming: false,
    pendingInterrupt: null,
    activeThreadId: null,

    async send(text) {
      const question = text.trim();
      if (!question || get().isStreaming || get().pendingInterrupt) return;

      const history = get()
        .messages.filter((m) => m.content && !m.error)
        .map((m) => ({ role: m.role, content: m.content }));

      // Fresh thread per turn so Sqlite checkpoints never collide across questions.
      const threadId = uid().replace(/-/g, "");

      set((s) => ({
        isStreaming: true,
        pendingInterrupt: null,
        activeThreadId: threadId,
        messages: [
          ...s.messages,
          { id: uid(), role: "user", content: question },
          { id: uid(), role: "assistant", content: "", streaming: true, steps: [] },
        ],
      }));

      const tokens = createTokenBatcher((chunk) => {
        patchLast((m) => ({ ...m, content: m.content + chunk }));
      });

      controller = new AbortController();
      let interrupted = false;
      try {
        for await (const ev of streamChat(
          [...history, { role: "user", content: question }],
          controller.signal,
          threadId,
        )) {
          if (applyStreamEvent(ev, tokens) === "interrupt") {
            interrupted = true;
            break;
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError")
          patchLast((m) => ({ ...m, error: (err as Error).message || "Could not reach the server." }));
      } finally {
        tokens.flushNow();
        if (!interrupted) {
          patchLast((m) => ({ ...m, streaming: false, awaitingApproval: false }));
          set({ isStreaming: false });
        }
        controller = null;
      }
    },

    async resolveInterrupt(decision) {
      const pending = get().pendingInterrupt;
      if (!pending || get().isStreaming) return;

      set({ isStreaming: true, pendingInterrupt: null });
      patchLast((m) => ({ ...m, streaming: true, awaitingApproval: false }));

      const tokens = createTokenBatcher((chunk) => {
        patchLast((m) => ({ ...m, content: m.content + chunk }));
      });

      controller = new AbortController();
      let interrupted = false;
      try {
        for await (const ev of streamChatResume(pending.thread_id, decision, controller.signal)) {
          if (applyStreamEvent(ev, tokens) === "interrupt") {
            interrupted = true;
            break;
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError")
          patchLast((m) => ({ ...m, error: (err as Error).message || "Could not resume the agent." }));
      } finally {
        tokens.flushNow();
        if (!interrupted) {
          patchLast((m) => ({ ...m, streaming: false, awaitingApproval: false }));
          set({ isStreaming: false });
        }
        controller = null;
      }
    },

    stop() {
      controller?.abort();
      set({ pendingInterrupt: null });
    },

    clear() {
      controller?.abort();
      set({
        messages: [],
        isStreaming: false,
        pendingInterrupt: null,
        activeThreadId: null,
      });
    },
  };
});
