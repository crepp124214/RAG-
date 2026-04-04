import { describe, expect, it, vi } from "vitest"

import { streamChat } from "@/services/chat"

describe("streamChat", () => {
  it("能正确解析 SSE 事件流", async () => {
    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            [
              'event: message_start\ndata: {"session_id":"session-1"}\n\n',
              'event: token\ndata: {"content":"你好"}\n\n',
              'event: citation\ndata: {"document_id":"doc-1","document_name":"指南","chunk_id":"chunk-1","content":"引用内容","page_number":1}\n\n',
              'event: message_end\ndata: {"answer":"你好","citations":[],"user_message_id":"user-1","assistant_message_id":"assistant-1","session_id":"session-1"}\n\n',
            ].join(""),
          ),
        )
        controller.close()
      },
    })

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        body: stream,
      }),
    )

    const events = []
    for await (const event of streamChat("session-1", "你好")) {
      events.push(event)
    }

    expect(events.map((event) => event.event)).toEqual([
      "message_start",
      "token",
      "citation",
      "message_end",
    ])
  })
})
