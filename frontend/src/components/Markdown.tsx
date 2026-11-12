"use client";

import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function MarkdownInner({ children }: { children: string }) {
  return (
    <div className="md break-words" dir="auto">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: (props) => <a {...props} target="_blank" rel="noopener noreferrer" />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}

/** Memoized so completed messages never re-parse markdown while a sibling streams. */
export const Markdown = memo(MarkdownInner);
Markdown.displayName = "Markdown";
