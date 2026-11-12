"use client";

import { ArrowUp, Square } from "lucide-react";
import { useRef, useState } from "react";
import { useChatStore } from "@/store/chat-store";

export function ChatInput() {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const { send, stop, isStreaming, pendingInterrupt } = useChatStore();
  const locked = isStreaming || Boolean(pendingInterrupt);

  const submit = () => {
    if (!value.trim() || locked) return;
    void send(value);
    setValue("");
    if (ref.current) ref.current.style.height = "auto";
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-5 pt-2">
      <div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-ink-900/80 p-2 shadow-soft backdrop-blur-xl focus-within:border-white/20">
        <textarea
          ref={ref}
          value={value}
          rows={1}
          dir="auto"
          aria-label="Message"
          placeholder="Ask about your PDFs, or anything that needs the web"
          className="max-h-48 min-h-[2.5rem] flex-1 resize-none bg-transparent px-2 py-2 text-mist-100 outline-none placeholder:text-mist-500 leading-relaxed"
          onChange={(e) => {
            setValue(e.target.value);
            e.target.style.height = "auto";
            e.target.style.height = `${e.target.scrollHeight}px`;
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              submit();
            }
          }}
        />
        {isStreaming ? (
          <button
            onClick={stop}
            aria-label="Stop generating"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/10 text-mist-100 transition hover:bg-white/15"
          >
            <Square className="h-3.5 w-3.5" fill="currentColor" />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!value.trim() || Boolean(pendingInterrupt)}
            aria-label="Send message"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-soft transition hover:brightness-110 disabled:from-ink-700 disabled:to-ink-700 disabled:text-mist-500 disabled:shadow-none"
          >
            <ArrowUp className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}
