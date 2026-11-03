"use client";

import { Eraser } from "lucide-react";
import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chat-store";
import { useDocumentStore } from "@/store/document-store";
import { ChatInput } from "./ChatInput";
import { MessageBubble } from "./MessageBubble";

const SUGGESTIONS = [
  "Summarize the key points of my document",
  "What is the latest news about OpenAI?",
  "Compare what my PDF says with current market data",
];

export function ChatWindow() {
  const { messages, send, clear, isStreaming } = useChatStore();
  const docCount = useDocumentStore((s) => s.documents.length);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-ink-800 px-5 py-3">
        <p className="text-sm text-mist-500">
          {docCount ? `${docCount} document${docCount > 1 ? "s" : ""} indexed` : "No documents yet, web search only"}
        </p>
        {messages.length > 0 && (
          <button onClick={clear} className="flex items-center gap-1.5 rounded-md px-2 py-1 text-sm text-mist-300 hover:bg-ink-800">
            <Eraser className="h-4 w-4" aria-hidden /> New chat
          </button>
        )}
      </header>

      <div className="scroll-thin flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-3xl space-y-8 px-4 py-8">
          {messages.length === 0 ? (
            <section className="pt-[12vh]">
              <h1 className="text-3xl font-semibold tracking-tight">Ask your documents. Or the internet.</h1>
              <p className="mt-3 max-w-xl leading-relaxed text-mist-300">
                Upload PDFs on the left. For every question the agent decides whether the answer is in your files,
                needs a live web search, or needs neither, and shows you what it chose.
              </p>
              <ul className="mt-8 grid gap-2 sm:grid-cols-3">
                {SUGGESTIONS.map((q) => (
                  <li key={q}>
                    <button
                      onClick={() => void send(q)}
                      disabled={isStreaming}
                      className="h-full w-full rounded-xl border border-ink-700 bg-ink-900/60 p-3 text-start text-sm text-mist-300 hover:border-ink-600 hover:text-mist-100"
                    >
                      {q}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : (
            messages.map((m) => <MessageBubble key={m.id} message={m} />)
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <ChatInput />
    </main>
  );
}
