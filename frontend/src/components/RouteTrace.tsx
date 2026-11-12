"use client";

import { FileText, Globe, MessageCircle } from "lucide-react";
import { memo } from "react";
import type { ChatMessage, Route } from "@/lib/types";

const META: Record<
  Route,
  {
    label: string;
    badge: string;
    Icon: typeof Globe;
  }
> = {
  pinecone: {
    label: "Searched your PDFs",
    badge: "bg-teal-500/10 text-teal-400 border-teal-500/30 shadow-[0_0_20px_rgba(45,212,191,0.12)]",
    Icon: FileText,
  },
  web: {
    label: "Searched the web",
    badge: "bg-purple-500/10 text-purple-400 border-purple-500/30 shadow-[0_0_20px_rgba(192,132,252,0.14)]",
    Icon: Globe,
  },
  direct: {
    label: "Answered directly",
    badge: "bg-indigo-500/10 text-indigo-300 border-indigo-500/30 shadow-[0_0_20px_rgba(129,140,248,0.12)]",
    Icon: MessageCircle,
  },
};

function isActivelySearching(message: ChatMessage): boolean {
  // Ping while the agent is retrieving / searching, before answer tokens arrive.
  return Boolean(message.streaming && !message.content);
}

/** The agent's decision, shown above each answer: where it looked, why, and what happened. */
function RouteTraceInner({ message }: { message: ChatMessage }) {
  if (!message.route) {
    return message.streaming ? (
      <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-mist-300 backdrop-blur-md">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mist-300/60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-mist-300" />
        </span>
        Deciding where to look…
      </div>
    ) : null;
  }

  const fellBack = message.steps?.some((s) => s.node === "web_search") && message.route === "pinecone";
  const displayRoute: Route = fellBack ? "web" : message.route;
  const { label, badge, Icon } = META[displayRoute];
  const title = fellBack ? "PDFs had no answer, searched the web" : label;
  const searching = isActivelySearching(message);

  return (
    <details className="group mb-3 text-sm">
      <summary className="flex cursor-pointer list-none flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium backdrop-blur-md ${badge}`}
        >
          {searching ? (
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-current" />
            </span>
          ) : (
            <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
          )}
          {title}
        </span>
        {message.reason && (
          <span className="max-w-full truncate text-xs text-mist-500">{message.reason}</span>
        )}
      </summary>
      <div className="mt-2 space-y-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2.5 text-xs text-mist-300 shadow-soft backdrop-blur-md">
        {message.searchQuery && (
          <p>
            <span className="text-mist-500">Query: </span>
            <span className="font-mono text-mist-100" dir="auto">
              {message.searchQuery}
            </span>
          </p>
        )}
        <ol className="space-y-1.5">
          <li className="flex gap-2">
            <span className="text-mist-500">•</span>
            Routed to {message.route}
          </li>
          {message.steps?.map((s, i) => (
            <li key={`${s.node}-${i}`} className="flex gap-2">
              <span className="text-mist-500">•</span>
              {s.label}
            </li>
          ))}
        </ol>
      </div>
    </details>
  );
}

export const RouteTrace = memo(RouteTraceInner);
RouteTrace.displayName = "RouteTrace";
