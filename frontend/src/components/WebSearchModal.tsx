"use client";

import { Globe2 } from "lucide-react";
import { useEffect, useRef } from "react";
import type { WebSearchInterrupt } from "@/lib/types";

interface Props {
  interrupt: WebSearchInterrupt;
  busy?: boolean;
  onApprove: () => void;
  onDecline: () => void;
}

export function WebSearchModal({ interrupt, busy, onApprove, onDecline }: Props) {
  const approveRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    approveRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !busy) onDecline();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [busy, onDecline]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#0B0D17]/80 p-4 backdrop-blur-md"
      role="dialog"
      aria-modal="true"
      aria-labelledby="web-search-title"
      aria-describedby="web-search-desc"
    >
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#151828] p-6 shadow-2xl">
        <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-purple-500/30 bg-purple-500/10 shadow-[0_0_24px_rgba(168,85,247,0.35)]">
          <Globe2 className="h-6 w-6 text-purple-300" aria-hidden />
        </div>

        <h2 id="web-search-title" className="text-lg font-bold text-white">
          Web Search Required
        </h2>
        <p id="web-search-desc" className="mt-2 text-sm leading-relaxed text-gray-400">
          {interrupt.message ||
            "The requested information is not available in your uploaded PDF. Would you like me to search the internet to find the answer?"}
        </p>

        {interrupt.search_query && (
          <p className="mt-3 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 font-mono text-xs text-mist-300" dir="auto">
            <span className="text-mist-500">Query · </span>
            {interrupt.search_query}
          </p>
        )}

        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            disabled={busy}
            onClick={onDecline}
            className="rounded-xl border border-white/20 px-4 py-2.5 text-sm text-gray-300 transition hover:bg-white/5 disabled:opacity-50"
          >
            No, Cancel
          </button>
          <button
            ref={approveRef}
            type="button"
            disabled={busy}
            onClick={onApprove}
            className="rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-[0_0_15px_rgba(147,51,234,0.5)] transition hover:shadow-[0_0_25px_rgba(147,51,234,0.7)] disabled:opacity-50"
          >
            Yes, Search Web
          </button>
        </div>
      </div>
    </div>
  );
}
