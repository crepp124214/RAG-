import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { useChatStore } from "@/stores/chat"

const serviceMocks = vi.hoisted(() => ({
  createSession: vi.fn(),
  fetchSessions: vi.fn(),
  fetchMessages: vi.fn(),
  streamChat: vi.fn(),
  updateSession: vi.fn(),
  deleteSession: vi.fn(),
  generateSessionTitle: vi.fn(),
  searchSessions: vi.fn(),
  exportSession: vi.fn(),
}))

vi.mock("@/services/chat", async () => {
  const actual = await vi.importActual<typeof import("@/services/chat")>("@/services/chat")
  return {
    ...actual,
    createSession: serviceMocks.createSession,
    fetchSessions: serviceMocks.fetchSessions,
    fetchMessages: serviceMocks.fetchMessages,
    streamChat: serviceMocks.streamChat,
    updateSession: serviceMocks.updateSession,
    deleteSession: serviceMocks.deleteSession,
    generateSessionTitle: serviceMocks.generateSessionTitle,
    searchSessions: serviceMocks.searchSessions,
    exportSession: serviceMocks.exportSession,
  }
})

describe("会话管理增强", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe("会话搜索", () => {
    it("应该能够按关键词搜索会话", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "项目文档",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
        {
          id: "session-2",
          title: "技术方案",
          is_pinned: false,
          created_at: "2026-04-02T10:00:00",
          updated_at: "2026-04-02T10:00:00",
        },
      ])

      const store = useChatStore()
      await store.loadSessions()

      store.setSearchKeyword("项目")

      expect(store.filteredSessions).toHaveLength(1)
      expect(store.filteredSessions[0].title).toBe("项目文档")
    })

    it("搜索关键词为空时应该返回所有会话", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "项目文档",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
        {
          id: "session-2",
          title: "技术方案",
          is_pinned: false,
          created_at: "2026-04-02T10:00:00",
          updated_at: "2026-04-02T10:00:00",
        },
      ])

      const store = useChatStore()
      await store.loadSessions()

      store.setSearchKeyword("")

      expect(store.filteredSessions).toHaveLength(2)
    })
  })

  describe("会话重命名", () => {
    it("应该能够重命名会话", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "旧标题",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
      ])

      serviceMocks.updateSession.mockResolvedValue({
        id: "session-1",
        title: "新标题",
        is_pinned: false,
        created_at: "2026-04-01T10:00:00",
        updated_at: "2026-04-01T10:05:00",
      })

      const store = useChatStore()
      await store.loadSessions()

      await store.renameSession("session-1", "新标题")

      expect(store.sessions[0].title).toBe("新标题")
      expect(serviceMocks.updateSession).toHaveBeenCalledWith("session-1", { title: "新标题" })
    })
  })

  describe("会话置顶", () => {
    it("应该能够置顶会话", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "普通会话",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
      ])

      serviceMocks.updateSession.mockResolvedValue({
        id: "session-1",
        title: "普通会话",
        is_pinned: true,
        created_at: "2026-04-01T10:00:00",
        updated_at: "2026-04-01T10:05:00",
      })

      const store = useChatStore()
      await store.loadSessions()

      await store.togglePinSession("session-1")

      expect(store.sessions[0].is_pinned).toBe(true)
      expect(serviceMocks.updateSession).toHaveBeenCalledWith("session-1", { is_pinned: true })
    })

    it("置顶的会话应该排在前面", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "普通会话",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
        {
          id: "session-2",
          title: "置顶会话",
          is_pinned: true,
          created_at: "2026-04-02T10:00:00",
          updated_at: "2026-04-02T10:00:00",
        },
      ])

      const store = useChatStore()
      await store.loadSessions()

      expect(store.sortedSessions[0].id).toBe("session-2")
      expect(store.sortedSessions[0].is_pinned).toBe(true)
    })
  })

  describe("会话删除", () => {
    it("应该能够删除会话", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "会话1",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
        {
          id: "session-2",
          title: "会话2",
          is_pinned: false,
          created_at: "2026-04-02T10:00:00",
          updated_at: "2026-04-02T10:00:00",
        },
      ])

      serviceMocks.deleteSession.mockResolvedValue(undefined)

      const store = useChatStore()
      await store.loadSessions()

      await store.deleteSession("session-1")

      expect(store.sessions).toHaveLength(1)
      expect(store.sessions[0].id).toBe("session-2")
      expect(serviceMocks.deleteSession).toHaveBeenCalledWith("session-1")
    })

    it("删除当前选中的会话后应该自动选择下一个会话", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "会话1",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
        {
          id: "session-2",
          title: "会话2",
          is_pinned: false,
          created_at: "2026-04-02T10:00:00",
          updated_at: "2026-04-02T10:00:00",
        },
      ])

      serviceMocks.fetchMessages.mockResolvedValue([])
      serviceMocks.deleteSession.mockResolvedValue(undefined)

      const store = useChatStore()
      await store.loadSessions()
      await store.selectSession("session-1")

      expect(store.selectedSessionId).toBe("session-1")

      await store.deleteSession("session-1")

      expect(store.selectedSessionId).toBe("session-2")
    })
  })

  describe("会话导出", () => {
    it("应该能够导出会话为 Markdown", async () => {
      serviceMocks.exportSession.mockResolvedValue("# 会话标题\n\n内容...")

      const store = useChatStore()
      const markdown = await store.exportSessionToMarkdown("session-1")

      expect(markdown).toBe("# 会话标题\n\n内容...")
      expect(serviceMocks.exportSession).toHaveBeenCalledWith("session-1")
    })
  })

  describe("自动生成标题", () => {
    it("应该能够自动生成会话标题", async () => {
      serviceMocks.fetchSessions.mockResolvedValue([
        {
          id: "session-1",
          title: "新会话",
          is_pinned: false,
          created_at: "2026-04-01T10:00:00",
          updated_at: "2026-04-01T10:00:00",
        },
      ])

      serviceMocks.generateSessionTitle.mockResolvedValue({
        id: "session-1",
        title: "自动生成的标题",
        is_pinned: false,
        created_at: "2026-04-01T10:00:00",
        updated_at: "2026-04-01T10:05:00",
      })

      const store = useChatStore()
      await store.loadSessions()

      await store.autoGenerateTitle("session-1")

      expect(store.sessions[0].title).toBe("自动生成的标题")
      expect(serviceMocks.generateSessionTitle).toHaveBeenCalledWith("session-1")
    })
  })
})
