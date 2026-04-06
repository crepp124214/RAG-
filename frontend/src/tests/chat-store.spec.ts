import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { useChatStore } from "@/stores/chat"

const serviceMocks = vi.hoisted(() => ({
  createSession: vi.fn(),
  fetchSessions: vi.fn(),
  fetchMessages: vi.fn(),
  streamChat: vi.fn(),
}))

vi.mock("@/services/chat", async () => {
  const actual = await vi.importActual<typeof import("@/services/chat")>("@/services/chat")
  return {
    ...actual,
    createSession: serviceMocks.createSession,
    fetchSessions: serviceMocks.fetchSessions,
    fetchMessages: serviceMocks.fetchMessages,
    streamChat: serviceMocks.streamChat,
  }
})

describe("useChatStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it("发送消息时会自动创建会话并写入流式回答", async () => {
    serviceMocks.createSession.mockResolvedValue({
      session_id: "session-1",
      title: "新会话",
    })
    serviceMocks.fetchSessions.mockResolvedValue([
      {
        id: "session-1",
        title: "项目里程碑总结",
        created_at: "2026-04-04T10:00:00",
        updated_at: "2026-04-04T10:01:00",
      },
    ])
    serviceMocks.fetchMessages.mockResolvedValue([])
    serviceMocks.streamChat.mockImplementation(async function* () {
      yield { event: "message_start", data: { session_id: "session-1" } }
      yield {
        event: "tool_call",
        data: {
          tool_name: "web_search",
          arguments: { query: "请总结一下" },
        },
      }
      yield {
        event: "tool_result",
        data: {
          tool_name: "web_search",
          arguments: { query: "请总结一下" },
          status: "success",
          result_summary: "命中 1 条搜索结果",
          error_code: null,
          error_detail: null,
        },
      }
      yield { event: "token", data: { content: "你好，" } }
      yield {
        event: "citation",
        data: {
          document_id: "doc-1",
          document_name: "开发手册",
          chunk_id: "chunk-1",
          content: "系统 A -> 依赖 -> 系统 B",
          page_number: 2,
          source_type: "graph",
          asset_label: null,
          preview_available: false,
          relation_label: "依赖",
          entity_path: "系统 A -> 系统 B",
        },
      }
      yield {
        event: "message_end",
        data: {
          answer: "你好，以下是结果",
          citations: [
            {
              document_id: "doc-1",
              document_name: "开发手册",
              chunk_id: "chunk-1",
              content: "系统 A -> 依赖 -> 系统 B",
              page_number: 2,
              source_type: "graph",
              asset_label: null,
              preview_available: false,
              relation_label: "依赖",
              entity_path: "系统 A -> 系统 B",
            },
          ],
          tool_calls: [
            {
              tool_name: "web_search",
              arguments: { query: "请总结一下" },
              status: "success",
              result_summary: "命中 1 条搜索结果",
              error_code: null,
              error_detail: null,
            },
          ],
          user_message_id: "user-1",
          assistant_message_id: "assistant-1",
          session_id: "session-1",
        },
      }
    })

    const store = useChatStore()
    await store.sendMessage("请总结一下")

    expect(store.selectedSessionId).toBe("session-1")
    expect(store.messages).toHaveLength(2)
    expect(store.messages[0].role).toBe("user")
    expect(store.messages[1].content).toBe("你好，以下是结果")
    expect(store.messages[1].citations).toHaveLength(1)
    expect(store.messages[1].citations[0].source_type).toBe("graph")
    expect(store.messages[1].citations[0].relation_label).toBe("依赖")
    expect(store.messages[1].citations[0].entity_path).toBe("系统 A -> 系统 B")
    expect(store.messages[1].toolCalls).toHaveLength(1)
    expect(store.messages[1].toolCalls[0].tool_name).toBe("web_search")
    expect(store.isSending).toBe(false)
  })

  it("在收到 tool_call 时会先写入 pending 工具卡片，再被 tool_result 更新", async () => {
    serviceMocks.createSession.mockResolvedValue({
      session_id: "session-1",
      title: "新会话",
    })
    serviceMocks.fetchSessions.mockResolvedValue([
      {
        id: "session-1",
        title: "项目里程碑总结",
        created_at: "2026-04-04T10:00:00",
        updated_at: "2026-04-04T10:01:00",
      },
    ])
    serviceMocks.fetchMessages.mockResolvedValue([])

    const store = useChatStore()

    serviceMocks.streamChat.mockImplementation(async function* () {
      yield { event: "message_start", data: { session_id: "session-1" } }
      yield {
        event: "tool_call",
        data: {
          tool_name: "web_search",
          arguments: { query: "请总结一下" },
        },
      }

      const assistantMessage = store.messages.find((message) => message.role === "assistant")
      expect(assistantMessage?.toolCalls).toHaveLength(1)
      expect(assistantMessage?.toolCalls[0].status).toBe("pending")
      expect(assistantMessage?.toolCalls[0].result_summary).toBeNull()

      yield {
        event: "tool_result",
        data: {
          tool_name: "web_search",
          arguments: { query: "请总结一下" },
          status: "success",
          result_summary: "命中 1 条搜索结果",
          error_code: null,
          error_detail: null,
        },
      }
      yield {
        event: "message_end",
        data: {
          answer: "你好，以下是结果",
          citations: [],
          tool_calls: [
            {
              tool_name: "web_search",
              arguments: { query: "请总结一下" },
              status: "success",
              result_summary: "命中 1 条搜索结果",
              error_code: null,
              error_detail: null,
            },
          ],
          user_message_id: "user-1",
          assistant_message_id: "assistant-1",
          session_id: "session-1",
        },
      }
    })

    await store.sendMessage("请总结一下")

    expect(store.messages[1].toolCalls).toHaveLength(1)
    expect(store.messages[1].toolCalls[0].status).toBe("success")
    expect(store.messages[1].toolCalls[0].result_summary).toBe("命中 1 条搜索结果")
  })

  it("加载历史消息时会恢复 citations 和 toolCalls", async () => {
    serviceMocks.fetchSessions.mockResolvedValue([
      {
        id: "session-1",
        title: "历史会话",
        created_at: "2026-04-04T10:00:00",
        updated_at: "2026-04-04T10:01:00",
      },
    ])
    serviceMocks.fetchMessages.mockResolvedValue([
      {
        id: "assistant-1",
        session_id: "session-1",
        role: "assistant",
        content: "历史回答",
        citations: [
          {
            document_id: "doc-1",
            document_name: "验收文档.txt",
            chunk_id: "chunk-1",
            content: "系统 A -> 依赖 -> 系统 B",
            page_number: 1,
            source_type: "graph",
            asset_label: null,
            preview_available: false,
            relation_label: "依赖",
            entity_path: "系统 A -> 系统 B",
          },
        ],
        tool_calls: [
          {
            tool_name: "document_lookup",
            arguments: { lookup_type: "content", query: "历史问题" },
            status: "success",
            result_summary: "命中 1 个文档片段",
            error_code: null,
            error_detail: null,
          },
        ],
        created_at: "2026-04-04T10:02:00",
        updated_at: "2026-04-04T10:02:00",
      },
    ])

    const store = useChatStore()
    await store.hydrate()

    expect(store.selectedSessionId).toBe("session-1")
    expect(store.messages).toHaveLength(1)
    expect(store.messages[0].citations[0].document_id).toBe("doc-1")
    expect(store.messages[0].citations[0].entity_path).toBe("系统 A -> 系统 B")
    expect(store.messages[0].toolCalls[0].tool_name).toBe("document_lookup")
  })
})
