export type SSEEvent = {
  event: string;
  data: Record<string, unknown>;
};

export type SSEHandlers = {
  onEvent: (event: SSEEvent) => void;
};

/**
 * Consumes a `fetch` streaming response as server-sent events.
 *
 * Uses `fetch` + `ReadableStream` rather than `EventSource` because chat
 * requests are POSTs with a body (EventSource only supports GET) — the same
 * reason Dify's `ssePost`/`handleStream` (web/service/base.ts) does it this
 * way. Line-buffer carryover (keep the last, possibly-incomplete line for
 * the next chunk) plus a swallowed `JSON.parse` failure are the two things
 * that make this robust against a chunk boundary landing mid-line or
 * mid-JSON-object — Dify relies on exactly the same two mechanisms.
 */
export async function parseSSEStream(
  response: Response,
  handlers: SSEHandlers,
  signal?: AbortSignal,
): Promise<void> {
  if (!response.body) {
    throw new Error("response has no body to stream");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    for (;;) {
      if (signal?.aborted) {
        await reader.cancel();
        return;
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      // Keep the trailing (possibly incomplete) line for the next chunk.
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;

        const payload = trimmed.slice("data:".length).trim();
        if (!payload || payload === "[DONE]") continue;

        try {
          const parsed = JSON.parse(payload) as { event?: string } & Record<string, unknown>;
          handlers.onEvent({ event: parsed.event ?? "message", data: parsed });
        } catch {
          // A JSON object split across two reads parses as garbage at this
          // point — treat it as "not enough bytes yet", not an error.
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
