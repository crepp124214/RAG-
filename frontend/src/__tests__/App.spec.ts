import { mount } from "@vue/test-utils"
import { createPinia, setActivePinia } from "pinia"
import ElementPlus from "element-plus"
import { beforeEach, describe, expect, it, vi } from "vitest"

import App from "@/App.vue"

const mockFetchHealth = vi.fn()

vi.mock("@/services/system", () => ({
  fetchHealth: () => mockFetchHealth(),
}))

describe("App", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockFetchHealth.mockReset()
  })

  it("渲染整体工作台布局并显示健康检查成功提示", async () => {
    mockFetchHealth.mockResolvedValue({
      status: "ok",
      app_name: "rag-system",
      app_env: "development",
    })

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), ElementPlus],
        stubs: {
          SessionSidebar: { template: "<div>会话列表区域</div>" },
          ChatWorkspacePanel: { template: "<div>聊天工作台区域</div>" },
          DocumentManagerPanel: { template: "<div>文档管理区域</div>" },
          TaskStatusPanel: { template: "<div>任务状态区域</div>" },
        },
      },
    })

    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.text()).toContain("RAG 智能文档检索助手")
    expect(wrapper.text()).toContain("会话列表区域")
    expect(wrapper.text()).toContain("聊天工作台区域")
    expect(wrapper.text()).toContain("文档管理区域")
    expect(wrapper.text()).toContain("任务状态区域")
    expect(wrapper.text()).toContain("后端连接成功")
  })

  it("在健康检查失败时显示错误提示", async () => {
    mockFetchHealth.mockRejectedValue(new Error("无法连接后端服务。"))

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), ElementPlus],
        stubs: {
          SessionSidebar: { template: "<div>会话列表区域</div>" },
          ChatWorkspacePanel: { template: "<div>聊天工作台区域</div>" },
          DocumentManagerPanel: { template: "<div>文档管理区域</div>" },
          TaskStatusPanel: { template: "<div>任务状态区域</div>" },
        },
      },
    })

    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.text()).toContain("后端连接失败")
    expect(wrapper.text()).toContain("无法连接后端服务。")
  })
})
