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
      yield { event: "token", data: { content: "你好，" } }
      yield {
        event: "citation",
        data: {
          document_id: "doc-1",
          document_name: "开发手册",
          chunk_id: "chunk-1",
          content: "这里是引用",
          page_number: 2,
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
              content: "这里是引用",
              page_number: 2,
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
    expect(store.isSending).toBe(false)
  })
})
