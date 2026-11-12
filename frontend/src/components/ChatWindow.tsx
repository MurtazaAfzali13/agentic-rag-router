"use client";

import { Eraser } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import { useChatStore } from "@/store/chat-store";
import { useDocumentStore } from "@/store/document-store";
import { ChatInput } from "./ChatInput";
import { MessageBubble } from "./MessageBubble";
import { WebSearchModal } from "./WebSearchModal";

const SUGGESTIONS = [
  "Summarize the key points of my document",
  "What is the latest news about OpenAI?",
  "Compare what my PDF says with current market data",
];

export function ChatWindow() {
  const { messages, send, clear, isStreaming, pendingInterrupt, resolveInterrupt } = useChatStore();
  const docCount = useDocumentStore((s) => s.documents.length);
  const scrollRef = useRef<HTMLDivElement>(null);
  const anchorRef = useRef<HTMLDivElement>(null);
  const stickToBottom = useRef(true);
  const scrollRaf = useRef(0);

  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
    stickToBottom.current = distance < 80;
  }, []);

  useEffect(() => {
    if (!stickToBottom.current) return;
    if (scrollRaf.current) cancelAnimationFrame(scrollRaf.current);
    scrollRaf.current = requestAnimationFrame(() => {
      const el = scrollRef.current;
      if (!el) return;
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    });
    return () => {
      if (scrollRaf.current) cancelAnimationFrame(scrollRaf.current);
    };
  }, [messages]);

  return (
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3 backdrop-blur-md">
        <p className="text-sm text-mist-500">
          {docCount
            ? `${docCount} document${docCount > 1 ? "s" : ""} indexed`
            : "No documents yet · web search only"}
        </p>
        {messages.length > 0 && (
          <button
            onClick={clear}
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-mist-300 transition hover:bg-white/5 hover:text-mist-100"
          >
            <Eraser className="h-4 w-4" aria-hidden /> New chat
          </button>
        )}
      </header>

      <div ref={scrollRef} onScroll={onScroll} className="scroll-thin chat-scroll flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-8">
          {messages.length === 0 ? (
            <section className="pt-[12vh]">
              <h1 className="text-3xl font-semibold tracking-tight text-white">
                Ask your documents. Or the internet.
              </h1>
              <p className="mt-3 max-w-xl text-mist-300 leading-relaxed">
                Upload PDFs on the left. For every question the agent decides whether the answer is in your
                files, needs a live web search, or needs neither — and shows you what it chose.
              </p>
              <ul className="mt-8 grid gap-2 sm:grid-cols-3">
                {SUGGESTIONS.map((q) => (
                  <li key={q}>
                    <button
                      onClick={() => void send(q)}
                      disabled={isStreaming || Boolean(pendingInterrupt)}
                      className="h-full w-full rounded-2xl border border-white/10 bg-white/[0.03] p-3.5 text-start text-sm text-mist-300 shadow-soft backdrop-blur-md transition hover:border-white/20 hover:bg-white/[0.06] hover:text-mist-100 disabled:opacity-50"
                    >
                      {q}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            messages.map((m, i) => {
              let userQuery = "";
              if (m.role !== "user") {
                for (let j = i - 1; j >= 0; j--) {
                  if (messages[j].role === "user") {
                    userQuery = messages[j].content;
                    break;
                  }
                }
              }
              return <MessageBubble key={m.id} message={m} userQuery={userQuery} />;
            })
          )}
          {/* Browser scroll anchoring target — keeps stream appends from jumping the viewport */}
          <div ref={anchorRef} aria-hidden style={{ overflowAnchor: "auto", height: 1 }} />
        </div>
      </div>

      <ChatInput />

      {pendingInterrupt && (
        <WebSearchModal
          interrupt={pendingInterrupt}
          busy={isStreaming}
          onApprove={() => void resolveInterrupt("YES")}
          onDecline={() => void resolveInterrupt("NO")}
        />
      )}
    </main>
  );
}
