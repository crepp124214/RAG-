import { createPinia, setActivePinia } from "pinia"
import ElementPlus from "element-plus"
import { mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"

import ChatWorkspacePanel from "@/components/chat/ChatWorkspacePanel.vue"
import { useChatStore } from "@/stores/chat"

describe("ChatWorkspacePanel", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("会将聊天区渲染为以会话头部和连续消息工作区为核心的主舞台", async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useChatStore()
    store.sessions = [
      {
        id: "session-stage-1",
        title: "产品路线讨论",
        created_at: "2026-04-07T09:00:00Z",
        updated_at: "2026-04-07T10:00:00Z",
      },
    ]
    store.selectedSessionId = "session-stage-1"
    store.messages = [
      {
        id: "user-stage-1",
        sessionId: "session-stage-1",
        role: "user",
        content: "请整理这个季度的发布重点。",
        createdAt: "2026-04-07T10:00:00Z",
        updatedAt: "2026-04-07T10:00:00Z",
        citations: [],
        toolCalls: [],
      },
      {
        id: "assistant-stage-1",
        sessionId: "session-stage-1",
        role: "assistant",
        content: "我已经整理出一版重点摘要。",
        createdAt: "2026-04-07T10:01:00Z",
        updatedAt: "2026-04-07T10:01:00Z",
        citations: [],
        toolCalls: [],
      },
    ]

    const wrapper = mount(ChatWorkspacePanel, {
      global: {
        plugins: [pinia, ElementPlus],
      },
    })

    expect(wrapper.text()).toContain("产品路线讨论")
    expect(wrapper.findAll("article")).toHaveLength(2)
    expect(wrapper.text()).toContain("请整理这个季度的发布重点。")
    expect(wrapper.text()).toContain("我已经整理出一版重点摘要。")
    expect(wrapper.find("textarea").exists()).toBe(true)
    expect(wrapper.find("button").exists()).toBe(true)
    expect(wrapper.text()).toContain("发送问题")
  })

  it("会渲染 pending 的工具调用卡片", async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useChatStore()
    store.messages = [
      {
        id: "assistant-1",
        sessionId: "session-1",
        role: "assistant",
        content: "正在查询...",
        createdAt: "2026-04-05T10:00:00Z",
        updatedAt: "2026-04-05T10:00:00Z",
        citations: [],
        toolCalls: [
          {
            tool_name: "web_search",
            arguments: { query: "今天最新消息" },
            status: "pending",
            result_summary: null,
            error_code: null,
            error_detail: null,
          },
        ],
        isStreaming: true,
      },
    ]

    const wrapper = mount(ChatWorkspacePanel, {
      global: {
        plugins: [pinia, ElementPlus],
      },
    })

    expect(wrapper.text()).toContain("web_search")
    expect(wrapper.text()).toContain("调用中")
    expect(wrapper.text()).toContain("工具调用中...")
  })

  it("会渲染视觉引用卡片标签", async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useChatStore()
    store.messages = [
      {
        id: "assistant-2",
        sessionId: "session-1",
        role: "assistant",
        content: "图表说明如下。",
        createdAt: "2026-04-06T10:00:00Z",
        updatedAt: "2026-04-06T10:00:00Z",
        toolCalls: [],
        citations: [
          {
            document_id: "doc-1",
            document_name: "季度报告.pdf",
            chunk_id: "chunk-visual-1",
            content: "柱状图显示第二季度销量最高。",
            page_number: 3,
            source_type: "image",
            asset_label: "第 3 页图片 1",
            preview_available: true,
          },
        ],
      },
    ]

    const wrapper = mount(ChatWorkspacePanel, {
      global: {
        plugins: [pinia, ElementPlus],
      },
    })

    expect(wrapper.text()).toContain("季度报告.pdf")
    expect(wrapper.text()).toContain("第 3 页图片 1")
    expect(wrapper.text()).toContain("柱状图显示第二季度销量最高。")
  })

  it("会渲染图谱引用标签和实体路径", async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useChatStore()
    store.messages = [
      {
        id: "assistant-3",
        sessionId: "session-1",
        role: "assistant",
        content: "系统依赖关系如下。",
        createdAt: "2026-04-06T10:05:00Z",
        updatedAt: "2026-04-06T10:05:00Z",
        toolCalls: [],
        citations: [
          {
            document_id: "doc-graph-1",
            document_name: "系统蓝图.txt",
            chunk_id: "chunk-graph-1",
            content: "系统 A -> 依赖 -> 系统 B",
            page_number: 4,
            source_type: "graph",
            asset_label: null,
            preview_available: false,
            relation_label: "依赖",
            entity_path: "系统 A -> 系统 B",
          },
        ],
      },
    ]

    const wrapper = mount(ChatWorkspacePanel, {
      global: {
        plugins: [pinia, ElementPlus],
      },
    })

    expect(wrapper.text()).toContain("系统蓝图.txt")
    expect(wrapper.text()).toContain("图谱引用")
    expect(wrapper.text()).toContain("系统 A -> 系统 B")
    expect(wrapper.text()).toContain("系统依赖关系如下。")
  })

  it("同一来源分块同时作为文本和图谱引用时不会产生重复 key 警告", async () => {
    const warnSpy = vi.spyOn(console, "warn").mockImplementation(() => undefined)
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useChatStore()
    store.messages = [
      {
        id: "assistant-4",
        sessionId: "session-1",
        role: "assistant",
        content: "系统依赖关系如下。",
        createdAt: "2026-04-06T10:10:00Z",
        updatedAt: "2026-04-06T10:10:00Z",
        toolCalls: [],
        citations: [
          {
            document_id: "doc-graph-1",
            document_name: "系统蓝图.txt",
            chunk_id: "chunk-shared-1",
            content: "系统 A 依赖系统 B。",
            page_number: 4,
            source_type: "text",
            asset_label: null,
            preview_available: false,
          },
          {
            document_id: "doc-graph-1",
            document_name: "系统蓝图.txt",
            chunk_id: "chunk-shared-1",
            content: "系统 A -> 依赖 -> 系统 B",
            page_number: 4,
            source_type: "graph",
            asset_label: null,
            preview_available: false,
            relation_label: "依赖",
            entity_path: "系统 A -> 系统 B",
          },
        ],
      },
    ]

    mount(ChatWorkspacePanel, {
      global: {
        plugins: [pinia, ElementPlus],
      },
    })

    expect(warnSpy).not.toHaveBeenCalledWith(expect.stringContaining("Duplicate keys"))
    warnSpy.mockRestore()
  })
})
