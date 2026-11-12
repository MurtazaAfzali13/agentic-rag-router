"use client";

import { useEffect } from "react";
import { useDocumentStore } from "@/store/document-store";
import { DocumentList } from "./DocumentList";
import { FileDropzone } from "./FileDropzone";

export function Sidebar() {
  const refresh = useDocumentStore((s) => s.refresh);
  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <aside className="hidden w-80 shrink-0 flex-col border-e border-white/[0.06] bg-ink-900/50 backdrop-blur-xl md:flex">
      <div className="px-5 pb-4 pt-5">
        <p className="text-lg font-semibold tracking-tight text-white">RAG Router</p>
        <p className="mt-0.5 text-xs text-mist-500">LangGraph · Pinecone · Tavily</p>
      </div>
      <div className="px-4">
        <FileDropzone />
      </div>
      <div className="mt-6 px-5 text-xs font-medium text-mist-500">Your documents</div>
      <div className="scroll-thin mt-2 flex-1 overflow-y-auto px-3 pb-4">
        <DocumentList />
      </div>
    </aside>
  );
}
