import { create } from "zustand";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";

export interface UploadItem { name: string; status: "uploading" | "error"; error?: string }

interface DocumentState {
  documents: DocumentInfo[];
  uploads: UploadItem[];
  loadError: string | null;
  refresh: () => Promise<void>;
  upload: (files: File[]) => Promise<void>;
  remove: (id: string) => Promise<void>;
  dismissUpload: (name: string) => void;
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  uploads: [],
  loadError: null,

  async refresh() {
    try {
      set({ documents: await listDocuments(), loadError: null });
    } catch {
      set({ loadError: "Backend unreachable. Check that the API is running." });
    }
  },

  async upload(files) {
    for (const file of files) {
      set((s) => ({ uploads: [...s.uploads.filter((u) => u.name !== file.name), { name: file.name, status: "uploading" }] }));
      try {
        const doc = await uploadDocument(file);
        set((s) => ({ documents: [doc, ...s.documents], uploads: s.uploads.filter((u) => u.name !== file.name) }));
      } catch (err) {
        set((s) => ({
          uploads: s.uploads.map((u) => (u.name === file.name ? { ...u, status: "error", error: (err as Error).message } : u)),
        }));
      }
    }
  },

  async remove(id) {
    const previous = get().documents;
    set({ documents: previous.filter((d) => d.id !== id) });
    try {
      await deleteDocument(id);
    } catch {
      set({ documents: previous });
    }
  },

  dismissUpload(name) {
    set((s) => ({ uploads: s.uploads.filter((u) => u.name !== name) }));
  },
}));
