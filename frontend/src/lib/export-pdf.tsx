import { flushSync } from "react-dom";
import { createRoot } from "react-dom/client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Source } from "@/lib/types";

const REPORT_CSS = `
.pdf-report, .pdf-report * {
  box-sizing: border-box;
  border-color: #E5E7EB;      /* html2canvas can't parse oklch()/lab() colors, so override Tailwind's default border color */
  outline-color: transparent;
  box-shadow: none;
}
.pdf-report {
  width: 794px; padding: 0; background: #FFFFFF; color: #1F2937;
  font-family: Inter, Arial, Tahoma, "Segoe UI", sans-serif;
  font-size: 13.5px; line-height: 1.65;
}
.pdf-report .hdr { display:flex; justify-content:space-between; align-items:flex-end;
  padding-bottom: 12px; border-bottom: 2px solid #4F46E5; margin-bottom: 20px; }
.pdf-report .hdr h1 { margin:0; font-size: 22px; font-weight: 700; color:#111827; letter-spacing:-0.01em; }
.pdf-report .hdr .meta { font-size: 11px; color:#6B7280; text-align:right; }
.pdf-report .label { font-size: 10px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  color:#6B7280; margin: 0 0 6px; }
.pdf-report .query { background:#F3F4F6; border-left: 4px solid #4F46E5; border-radius: 6px;
  padding: 12px 14px; margin-bottom: 22px; white-space: pre-wrap; color:#111827; font-weight:500; }
.pdf-report .md { word-wrap: break-word; overflow-wrap: anywhere; }
.pdf-report .md p, .pdf-report .md li, .pdf-report .md h1, .pdf-report .md h2,
.pdf-report .md h3, .pdf-report .md h4, .pdf-report .md blockquote,
.pdf-report .md td, .pdf-report .md th { unicode-bidi: plaintext; }  /* Persian/English per paragraph */
.pdf-report .md > :first-child { margin-top: 0; }
.pdf-report .md p { margin: 0 0 10px; }
.pdf-report .md h1 { font-size: 19px; margin: 20px 0 8px; color:#111827; }
.pdf-report .md h2 { font-size: 16.5px; margin: 18px 0 8px; color:#111827; }
.pdf-report .md h3 { font-size: 14.5px; margin: 14px 0 6px; color:#111827; }
.pdf-report .md strong { font-weight: 700; color:#111827; }
.pdf-report .md ul, .pdf-report .md ol { margin: 0 0 10px; padding-inline-start: 22px; }
.pdf-report .md li { margin: 3px 0; }
.pdf-report .md a { color:#4338CA; text-decoration: underline; }
.pdf-report .md blockquote { margin: 10px 0; padding: 6px 14px; border-inline-start: 3px solid #D1D5DB;
  color:#4B5563; background:#F9FAFB; }
.pdf-report .md code { font-family: "JetBrains Mono", Consolas, "Courier New", monospace; font-size: 12px;
  background:#F3F4F6; color:#B91C1C; padding: 1px 5px; border-radius: 4px; }
.pdf-report .md pre { background:#F8FAFC; border:1px solid #E5E7EB; border-radius:8px; padding: 12px 14px;
  margin: 10px 0 14px; white-space: pre-wrap; word-break: break-word; unicode-bidi: normal; direction:ltr; text-align:left; }
.pdf-report .md pre code { background: transparent; color:#1F2937; padding:0; font-size: 11.5px; }
.pdf-report .md table { border-collapse: collapse; width:100%; margin: 10px 0 14px; font-size: 12.5px; }
.pdf-report .md th, .pdf-report .md td { border:1px solid #E5E7EB; padding: 6px 10px; text-align: start; }
.pdf-report .md th { background:#F3F4F6; font-weight:700; }
.pdf-report .md hr { border:0; border-top:1px solid #E5E7EB; margin: 16px 0; }
.pdf-report .src { margin-top: 22px; padding-top: 12px; border-top: 1px solid #E5E7EB; }
.pdf-report .src ol { margin:0; padding-inline-start: 20px; font-size: 11.5px; color:#4B5563; }
.pdf-report .src li { margin: 3px 0; word-break: break-all; }
`;

interface ReportProps {
  userQuery: string;
  aiResponse: string;
  sources: Source[];
  generatedAt: string;
}

function Report({ userQuery, aiResponse, sources, generatedAt }: ReportProps) {
  return (
    <div className="pdf-report">
      <style>{REPORT_CSS}</style>

      <div className="hdr">
        <h1>LangGraph Intelligence Report</h1>
        <div className="meta">{generatedAt}</div>
      </div>

      {userQuery && (
        <>
          <p className="label">User Query</p>
          <div className="query" dir="auto">
            {userQuery}
          </div>
        </>
      )}

      <p className="label">AI Response</p>
      <div className="md" dir="auto">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{aiResponse}</ReactMarkdown>
      </div>

      {sources.length > 0 && (
        <div className="src">
          <p className="label">Sources</p>
          <ol>
            {sources.map((s, i) => (
              <li key={i}>
                {s.title}
                {s.type === "pdf" ? ` — page ${s.page}` : s.url ? ` — ${s.url}` : ""}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

export async function exportToPDF(
  messageId: string,
  userQuery: string,
  aiResponse: string,
  sources: Source[] = [],
): Promise<void> {
  // Loaded lazily: html2pdf touches `window`, so it must never run during SSR.
  const html2pdf = (await import("html2pdf.js")).default;

  const now = new Date();
  const generatedAt = now.toLocaleString("en-US", { dateStyle: "long", timeStyle: "short" });
  const stamp = now.toISOString().slice(0, 10);

  // 1. Hidden host in the DOM (off-screen, but still laid out so html2canvas can measure it)
  const host = document.createElement("div");
  host.setAttribute("aria-hidden", "true");
  host.style.cssText = "position:fixed;top:0;left:-10000px;width:794px;background:#fff;pointer-events:none;";
  document.body.appendChild(host);

  const root = createRoot(host);
  try {
    // 2. Inject the content synchronously
    flushSync(() => root.render(<Report {...{ userQuery, aiResponse, sources, generatedAt }} />));
    await document.fonts?.ready;

    // 3. Generate the PDF
    await html2pdf()
      .set({
        margin: [14, 14, 18, 14], // mm: top, left, bottom, right
        filename: `langgraph-report-${messageId.slice(0, 8)}-${stamp}.pdf`,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, backgroundColor: "#FFFFFF", windowWidth: 794 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
        pagebreak: { mode: ["css", "legacy"], avoid: ["pre", "tr", "blockquote", "h1", "h2", "h3", "li"] },
      })
      .from(host.firstElementChild as HTMLElement)
      .toPdf()
      .get("pdf")
      .then((pdf: any) => {
        // Footer: "Page X of Y"
        const total = pdf.internal.getNumberOfPages();
        const w = pdf.internal.pageSize.getWidth();
        const h = pdf.internal.pageSize.getHeight();
        for (let i = 1; i <= total; i++) {
          pdf.setPage(i);
          pdf.setFontSize(8);
          pdf.setTextColor(120);
          pdf.text(`Page ${i} of ${total}`, w / 2, h - 8, { align: "center" });
        }
      })
      .save();
  } finally {
    // 4. Destroy the hidden div
    root.unmount();
    host.remove();
  }
}