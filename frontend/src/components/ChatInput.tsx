"use client";

import { ArrowUp, Square } from "lucide-react";
import { useRef, useState } from "react";
import { useChatStore } from "@/store/chat-store";

export function ChatInput() {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);
  const { send, stop, isStreaming } = useChatStore();

  const submit = () => {
    if (!value.trim() || isStreaming) return;
    void send(value);
    setValue("");
    if (ref.current) ref.current.style.height = "auto";
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-5">
      <div className="flex items-end gap-2 rounded-2xl border border-ink-700 bg-ink-900 p-2 focus-within:border-ink-600">
        <textarea
          ref={ref}
          value={value}
          rows={1}
          dir="auto"
          aria-label="Message"
          placeholder="Ask about your PDFs, or anything that needs the web"
          className="max-h-48 min-h-[2.5rem] flex-1 resize-none bg-transparent px-2 py-2 outline-none placeholder:text-mist-500"
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
          <button onClick={stop} aria-label="Stop generating" className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-ink-700 hover:bg-ink-600">
            <Square className="h-4 w-4" fill="currentColor" />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!value.trim()}
            aria-label="Send message"
            className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-pdf text-ink-950 transition disabled:bg-ink-700 disabled:text-mist-500"
          >
            <ArrowUp className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}
