export type Route = "pinecone" | "web" | "direct";

export interface Source {
  type: "pdf" | "web";
  title: string;
  url?: string;
  page?: number;
  score?: number;
  snippet: string;
}

export interface TraceStep { node: string; label: string }

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  route?: Route;
  reason?: string;
  searchQuery?: string;
  steps?: TraceStep[];
  sources?: Source[];
  streaming?: boolean;
  error?: string;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
  size_bytes: number;
  uploaded_at: string;
}

export type StreamEvent =
  | { event: "route"; data: { route: Route; reason: string; search_query: string } }
  | { event: "step"; data: TraceStep }
  | { event: "sources"; data: { sources: Source[] } }
  | { event: "token"; data: { text: string } }
  | { event: "done"; data: Record<string, never> }
  | { event: "error"; data: { message: string } };
