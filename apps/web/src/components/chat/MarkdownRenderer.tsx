import { code as shikiCodePlugin } from "@streamdown/code";
import { Streamdown } from "streamdown";
import "streamdown/styles.css";

type MarkdownRendererProps = {
  content: string;
  isStreaming?: boolean;
};

/**
 * Thin wrapper around Streamdown, the same streaming-safe markdown renderer
 * Dify uses (web/app/components/base/chat/markdown/). Streamdown's own
 * tokenizer terminates unmatched markdown (an unclosed code fence or bold
 * marker mid-stream) — Dify writes no custom balancing logic for this, it
 * just always renders through Streamdown in "streaming" mode, and this
 * component does the same.
 */
export function MarkdownRenderer({ content, isStreaming = false }: MarkdownRendererProps) {
  return (
    <Streamdown
      mode={isStreaming ? "streaming" : "static"}
      plugins={{ code: shikiCodePlugin }}
      controls={{ code: { copy: true } }}
      className="max-w-none font-body text-[14.5px] leading-relaxed text-text"
    >
      {content}
    </Streamdown>
  );
}
