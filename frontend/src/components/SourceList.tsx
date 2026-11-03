import { ExternalLink, FileText } from "lucide-react";
import type { Source } from "@/lib/types";

export function SourceList({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-medium text-mist-500">Sources</p>
      <ul className="grid gap-2 sm:grid-cols-2">
        {sources.map((s, i) => {
          const body = (
            <>
              <div className="flex items-center gap-2 text-xs">
                <span className="font-mono text-mist-500">[{i + 1}]</span>
                {s.type === "pdf" ? (
                  <FileText className="h-3.5 w-3.5 shrink-0 text-pdf" aria-hidden />
                ) : (
                  <ExternalLink className="h-3.5 w-3.5 shrink-0 text-web" aria-hidden />
                )}
                <span className="truncate font-medium text-mist-100">{s.title}</span>
              </div>
              <p className="mt-1 text-xs text-mist-500">
                {s.type === "pdf" ? `Page ${s.page}${s.score ? ` · match ${Math.round(s.score * 100)}%` : ""}` : hostname(s.url)}
              </p>
              <p className="mt-1.5 line-clamp-2 text-xs text-mist-300" dir="auto">{s.snippet}</p>
            </>
          );
          const cls = "block rounded-lg border border-ink-700 bg-ink-900/60 p-2.5";
          return (
            <li key={i}>
              {s.url ? (
                <a href={s.url} target="_blank" rel="noopener noreferrer" className={`${cls} hover:border-ink-600`}>
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
