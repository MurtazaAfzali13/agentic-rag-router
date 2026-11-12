export type Route = "pinecone" | "web" | "direct";

export interface Source {
  type: "pdf" | "web";
  title: string;
  url?: string;
  page?: number;
  score?: number;
  snippet: string;
  /** 1-based citation number from the backend (optional for older payloads). */
  n?: number;
  doc_id?: string;
  chunk_index?: number;
  text?: string;
  rects?: { x: number; y: number; w: number; h: number }[];
  page_width?: number;
  page_height?: number;
  match_quality?: number;
}

export interface TraceStep {
  node: string;
  label: string;
}

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
  awaitingApproval?: boolean;
  error?: string;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  pages: number;
  chunks: number;
  size_bytes: number;
  uploaded_at: string;
  has_file?: boolean;
}

export interface WebSearchInterrupt {
  thread_id: string;
  type: string;
  message: string;
  search_query?: string;
  reason?: string;
  route?: Route;
}

export type StreamEvent =
  | {
      event: "route";
      data: { route: Route; reason: string; search_query: string; thread_id?: string; t?: number };
    }
  | { event: "step"; data: TraceStep & { t?: number } }
  | { event: "sources"; data: { sources: Source[]; t?: number } }
  | { event: "token"; data: { text: string; t?: number } }
  | {
      event: "interrupt";
      data: WebSearchInterrupt & { t?: number };
    }
  | {
      event: "done";
      data: {
        thread_id?: string;
        used_citations?: number[];
        citations_valid?: boolean;
        t?: number;
      };
    }
  | { event: "error"; data: { message: string; thread_id?: string; t?: number } };
