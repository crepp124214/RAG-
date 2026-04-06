import { createPinia, setActivePinia } from "pinia"
import ElementPlus from "element-plus"
import { mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it } from "vitest"

import ChatWorkspacePanel from "@/components/chat/ChatWorkspacePanel.vue"
import { useChatStore } from "@/stores/chat"

describe("ChatWorkspacePanel", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
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
})
