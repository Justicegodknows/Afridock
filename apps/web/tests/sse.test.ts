import { describe, expect, it } from "vitest";

import { parseSSEStream } from "../src/lib/sse";

function makeResponse(chunks: string[]): Response {
  const encoder = new TextEncoder();
  let index = 0;
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]));
        index += 1;
      } else {
        controller.close();
      }
    },
  });
  return new Response(stream);
}

describe("parseSSEStream", () => {
  it("parses complete SSE lines into events", async () => {
    const response = makeResponse([
      `data: {"event":"message","delta":"He"}\n`,
      `data: {"event":"message","delta":"llo"}\n`,
    ]);

    const events: string[] = [];
    await parseSSEStream(response, {
      onEvent: ({ data }) => events.push(data.delta as string),
    });

    expect(events).toEqual(["He", "llo"]);
  });

  it("recovers when a chunk boundary splits a line mid-JSON", async () => {
    const response = makeResponse([`data: {"event":"message","del`, `ta":"split"}\n`]);

    const events: string[] = [];
    await parseSSEStream(response, {
      onEvent: ({ data }) => events.push(data.delta as string),
    });

    expect(events).toEqual(["split"]);
  });

  it("ignores comment lines and the [DONE] sentinel", async () => {
    const response = makeResponse([
      `: heartbeat\n`,
      `data: {"event":"message","delta":"x"}\n`,
      `data: [DONE]\n`,
    ]);

    const events: string[] = [];
    await parseSSEStream(response, {
      onEvent: ({ data }) => events.push(data.delta as string),
    });

    expect(events).toEqual(["x"]);
  });
});
