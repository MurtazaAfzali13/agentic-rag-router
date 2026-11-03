import { FileText, Globe, MessageCircle } from "lucide-react";
import type { ChatMessage, Route } from "@/lib/types";

const META: Record<Route, { label: string; color: string; Icon: typeof Globe }> = {
  pinecone: { label: "Searched your PDFs", color: "text-pdf", Icon: FileText },
  web: { label: "Searched the web", color: "text-web", Icon: Globe },
  direct: { label: "Answered directly", color: "text-direct", Icon: MessageCircle },
};

/** The agent's decision, shown above each answer: where it looked, why, and what happened. */
export function RouteTrace({ message }: { message: ChatMessage }) {
  if (!message.route) {
    return message.streaming ? <p className="mb-3 text-xs text-mist-500">Deciding where to look…</p> : null;
  }
  const { label, color, Icon } = META[message.route];
  const fellBack = message.steps?.some((s) => s.node === "web_search") && message.route === "pinecone";

  return (
    <details className="group mb-3 rounded-lg border border-ink-700 bg-ink-900/60 text-sm open:bg-ink-900">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 text-mist-300">
        <Icon className={`h-4 w-4 shrink-0 ${color}`} aria-hidden />
        <span className={`font-medium ${color}`}>{fellBack ? "PDFs had no answer, searched the web" : label}</span>
        <span className="truncate text-mist-500">{message.reason}</span>
      </summary>
      <div className="space-y-2 border-t border-ink-700 px-3 py-2.5 text-xs text-mist-300">
        {message.searchQuery && (
          <p>
            <span className="text-mist-500">Query: </span>
            <span className="font-mono" dir="auto">{message.searchQuery}</span>
          </p>
        )}
        <ol className="space-y-1">
          <li className="flex gap-2"><span className={color}>•</span>Routed to {message.route}</li>
          {message.steps?.map((s, i) => (
            <li key={i} className="flex gap-2"><span className={color}>•</span>{s.label}</li>
          ))}
        </ol>
      </div>
    </details>
  );
}
