import { AlertCircle } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { Markdown } from "./Markdown";
import { RouteTrace } from "./RouteTrace";
import { SourceList } from "./SourceList";

export function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-ink-700 px-4 py-2.5 leading-relaxed" dir="auto">
          {message.content}
        </p>
      </div>
    );
  }

  return (
    <article className="max-w-full">
      <RouteTrace message={message} />
      {message.content ? (
        <div className={message.streaming ? "caret" : ""}>
          <Markdown>{message.content}</Markdown>
        </div>
      ) : (
        message.streaming && message.route && <span className="caret text-mist-500" />
      )}
      {message.error && (
        <p role="alert" className="mt-3 flex items-start gap-2 rounded-lg border border-warn/40 bg-warn/10 px-3 py-2 text-sm text-warn">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          {message.error}
        </p>
      )}
      {!message.streaming && <SourceList sources={message.sources ?? []} />}
    </article>
  );
}
