"use client";

import { Loader2, UploadCloud, X } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { useDocumentStore } from "@/store/document-store";

export function FileDropzone() {
  const { upload, uploads, dismissUpload } = useDocumentStore();
  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    accept: { "application/pdf": [".pdf"] },
    maxSize: 25 * 1024 * 1024,
    onDropAccepted: (files) => void upload(files),
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-xl border border-dashed px-4 py-6 text-center transition ${
          isDragActive ? "border-pdf bg-pdf/10" : "border-ink-600 hover:border-mist-500"
        }`}
      >
        <input {...getInputProps()} aria-label="Upload PDF files" />
        <UploadCloud className="mx-auto h-6 w-6 text-mist-300" aria-hidden />
        <p className="mt-2 text-sm font-medium">{isDragActive ? "Drop to upload" : "Drop PDFs here"}</p>
        <p className="mt-0.5 text-xs text-mist-500">or click to browse, up to 25 MB each</p>
      </div>

      {fileRejections.length > 0 && (
        <p role="alert" className="mt-2 text-xs text-warn">Only PDF files up to 25 MB are accepted.</p>
      )}

      <ul className="mt-2 space-y-1.5">
        {uploads.map((u) => (
          <li key={u.name} className="flex items-start gap-2 rounded-lg bg-ink-800 px-3 py-2 text-xs">
            {u.status === "uploading" ? (
              <Loader2 className="mt-0.5 h-3.5 w-3.5 shrink-0 animate-spin text-pdf" aria-hidden />
            ) : (
              <X className="mt-0.5 h-3.5 w-3.5 shrink-0 text-warn" aria-hidden />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate">{u.status === "uploading" ? `Indexing ${u.name}…` : u.name}</p>
              {u.error && <p className="mt-0.5 text-warn">{u.error}</p>}
            </div>
            {u.status === "error" && (
              <button onClick={() => dismissUpload(u.name)} aria-label={`Dismiss ${u.name}`} className="text-mist-500 hover:text-mist-100">
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
