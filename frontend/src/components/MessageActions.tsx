"use client";

import { Check, Copy, FileDown, Loader2, ThumbsDown, ThumbsUp } from "lucide-react";
import { memo, useEffect, useRef, useState } from "react";
import { exportToPDF } from "@/lib/export-pdf";
import type { ChatMessage } from "@/lib/types";

const btn =
  "inline-flex items-center gap-1.5 rounded-md bg-transparent px-2.5 py-1.5 text-sm text-gray-400 " +
  "transition-all hover:bg-white/10 hover:text-white " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 " +
  "disabled:cursor-not-allowed disabled:opacity-50";

function MessageActionsInner({ message, userQuery }: { message: ChatMessage; userQuery: string }) {
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearCopyTimer = () => {
    if (timer.current !== null) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  };
  useEffect(() => {
    return () => {
      if (timer.current !== null) clearTimeout(timer.current);
    };
  }, []);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
    } catch {
      // Fallback for non-secure contexts / older browsers
      const ta = document.createElement("textarea");
      ta.value = message.content;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(true);
    clearCopyTimer();
    timer.current = setTimeout(() => setCopied(false), 2000);
  };

  const exportPdf = async () => {
    if (exporting) return;
    setExporting(true);
    try {
      await exportToPDF(message.id, userQuery, message.content, message.sources ?? []);
    } catch (err) {
      console.error("PDF export failed", err);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="mt-2 flex items-center gap-4" role="toolbar" aria-label="Response actions">
      <button onClick={copy} className={btn} title={copied ? "Copied!" : "Copy response text"} aria-live="polite">
        {copied ? <Check className="h-4 w-4 text-emerald-400" aria-hidden /> : <Copy className="h-4 w-4" aria-hidden />}
        {copied ? "Copied!" : "Copy Text"}
      </button>

      <button onClick={exportPdf} disabled={exporting} className={btn} title="Download response as PDF">
        {exporting ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
        ) : (
          <FileDown className="h-4 w-4" aria-hidden />
        )}
        {exporting ? "Exporting…" : "Export PDF"}
      </button>

      <div className="flex items-center gap-1">
        <button
          onClick={() => setFeedback((f) => (f === "up" ? null : "up"))}
          aria-pressed={feedback === "up"}
          aria-label="Good response"
          title="Good response"
          className={`${btn} ${feedback === "up" ? "!text-white bg-white/10" : ""}`}
        >
          <ThumbsUp className="h-4 w-4" />
        </button>
        <button
          onClick={() => setFeedback((f) => (f === "down" ? null : "down"))}
          aria-pressed={feedback === "down"}
          aria-label="Bad response"
          title="Bad response"
          className={`${btn} ${feedback === "down" ? "!text-white bg-white/10" : ""}`}
        >
          <ThumbsDown className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}

export const MessageActions = memo(MessageActionsInner);
MessageActions.displayName = "MessageActions";