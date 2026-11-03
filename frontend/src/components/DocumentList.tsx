"use client";

import { FileText, Trash2 } from "lucide-react";
import { useDocumentStore } from "@/store/document-store";

const size = (b: number) => (b > 1_000_000 ? `${(b / 1_000_000).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1000))} KB`);

export function DocumentList() {
  const { documents, remove, loadError } = useDocumentStore();

  if (loadError) return <p role="alert" className="text-xs text-warn">{loadError}</p>;
  if (!documents.length) return <p className="text-xs text-mist-500">Nothing uploaded yet.</p>;

  return (
    <ul className="space-y-1.5">
      {documents.map((d) => (
        <li key={d.id} className="group flex items-center gap-2.5 rounded-lg px-2.5 py-2 hover:bg-ink-800">
          <FileText className="h-4 w-4 shrink-0 text-pdf" aria-hidden />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm" title={d.filename}>{d.filename}</p>
            <p className="text-xs text-mist-500">{d.pages} pages · {d.chunks} chunks · {size(d.size_bytes)}</p>
          </div>
          <button
            onClick={() => void remove(d.id)}
            aria-label={`Delete ${d.filename}`}
            className="rounded-md p-1.5 text-mist-500 opacity-0 hover:bg-ink-700 hover:text-warn focus-visible:opacity-100 group-hover:opacity-100"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}
