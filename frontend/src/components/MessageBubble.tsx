"use client";

import { AlertCircle } from "lucide-react";
import { memo } from "react";
import type { ChatMessage } from "@/lib/types";
import { Markdown } from "./Markdown";
import { RouteTrace } from "./RouteTrace";
import { SourceList } from "./SourceList";
import { MessageActions } from "./MessageActions";

function TypingDots() {
  return (
    <span className="typing-dots ml-1 inline-flex items-center text-mist-500" aria-hidden>
      <span />
      <span />
      <span />
    </span>
  );
}

function MessageBubbleInner({ message, userQuery = "" }: { message: ChatMessage; userQuery?: string }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p
          className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-white shadow-soft leading-relaxed"
          dir="auto"
        >
          {message.content}
        </p>
      </div>
    );
  }

  const showCaret = Boolean(message.streaming && message.content);
  const showWaiting = Boolean(message.streaming && !message.content);
  const showApprovalWait = Boolean(message.awaitingApproval && !message.content);
  const showActions = !message.streaming && !message.awaitingApproval && Boolean(message.content);

  return (
    <div className="max-w-full">
      <article className="max-w-full rounded-2xl border border-white/10 bg-white/[0.04] p-4 shadow-glass backdrop-blur-md transition-[min-height] duration-150 ease-out">
        <RouteTrace message={message} />

        {message.content ? (
          <div className={`min-h-[1.5em] leading-relaxed ${showCaret ? "stream-caret" : ""}`}>
            <Markdown>{message.content}</Markdown>
          </div>
        ) : showApprovalWait ? (
          <p className="text-sm text-purple-300/90" aria-live="polite">
            Waiting for your decision on a web search…
          </p>
        ) : (
          showWaiting && (
            <p className="flex items-center gap-2 text-sm text-mist-500" aria-live="polite">
              {message.route ? "Writing answer" : "Thinking"}
              <TypingDots />
            </p>
          )
        )}

        {message.error && (
          <p
            role="alert"
            className="mt-3 flex items-start gap-2 rounded-xl border border-warn/40 bg-warn/10 px-3 py-2 text-sm text-warn"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            {message.error}
          </p>
        )}

        {!message.streaming && !message.awaitingApproval && <SourceList sources={message.sources ?? []} />}
      </article>

      {showActions && <MessageActions message={message} userQuery={userQuery} />}
    </div>
  );
}

export const MessageBubble = memo(MessageBubbleInner);
MessageBubble.displayName = "MessageBubble";