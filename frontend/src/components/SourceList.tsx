import { ExternalLink, FileText } from "lucide-react";
import { memo } from "react";
import type { Source } from "@/lib/types";

function SourceListInner({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="mt-4 border-t border-white/[0.06] pt-4">
      <p className="mb-2 text-xs font-medium text-mist-500">Sources</p>
      <ul className="grid gap-2 sm:grid-cols-2">
        {sources.map((s, i) => {
          const body = (
            <>
              <div className="flex items-center gap-2 text-xs">
                <span className="font-mono text-mist-500">[{typeof s.n === "number" ? s.n : i + 1}]</span>
                {s.type === "pdf" ? (
                  <FileText className="h-3.5 w-3.5 shrink-0 text-teal-400" aria-hidden />
                ) : (
                  <ExternalLink className="h-3.5 w-3.5 shrink-0 text-purple-400" aria-hidden />
                )}
                <span className="truncate font-medium text-mist-100">{s.title}</span>
              </div>
              <p className="mt-1 text-xs text-mist-500">
                {s.type === "pdf"
                  ? `Page ${s.page}${s.score ? ` · match ${Math.round(s.score * 100)}%` : ""}`
                  : hostname(s.url)}
              </p>
              <p className="mt-1.5 line-clamp-2 text-xs text-mist-300 leading-relaxed" dir="auto">
                {s.snippet}
              </p>
            </>
          );
          const cls =
            "block rounded-xl border border-white/10 bg-white/[0.03] p-2.5 transition hover:border-white/20 hover:bg-white/[0.05]";
          return (
            <li key={`${s.type}-${s.n ?? i}-${s.title}`}>
              {s.url ? (
                <a href={s.url} target="_blank" rel="noopener noreferrer" className={cls}>
                  {body}
                </a>
              ) : (
                <div className={cls}>{body}</div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function hostname(url?: string) {
  try {
    return url ? new URL(url).hostname.replace(/^www\./, "") : "";
  } catch {
    return url ?? "";
  }
}

export const SourceList = memo(SourceListInner);
SourceList.displayName = "SourceList";
