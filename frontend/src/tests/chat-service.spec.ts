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
              'event: tool_call\ndata: {"tool_name":"web_search","arguments":{"query":"你好"}}\n\n',
              'event: tool_result\ndata: {"tool_name":"web_search","arguments":{"query":"你好"},"status":"success","result_summary":"命中 1 条搜索结果","error_code":null,"error_detail":null}\n\n',
              'event: token\ndata: {"content":"你好"}\n\n',
              'event: citation\ndata: {"document_id":"doc-1","document_name":"指南","chunk_id":"chunk-1","content":"引用内容","page_number":1,"source_type":"image","asset_label":"第 1 页图片 1","preview_available":true}\n\n',
              'event: message_end\ndata: {"answer":"你好","citations":[],"tool_calls":[{"tool_name":"web_search","arguments":{"query":"你好"},"status":"success","result_summary":"命中 1 条搜索结果","error_code":null,"error_detail":null}],"user_message_id":"user-1","assistant_message_id":"assistant-1","session_id":"session-1"}\n\n',
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
      "tool_call",
      "tool_result",
      "token",
      "citation",
      "message_end",
    ])
  })
})
