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

  it("渲染基础工作台布局并显示健康成功提示", async () => {
    mockFetchHealth.mockResolvedValue({
      status: "ok",
      app_name: "rag-system",
      app_env: "development",
    })

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })

    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.text()).toContain("RAG 智能文档检索助手")
    expect(wrapper.text()).toContain("会话列表")
    expect(wrapper.text()).toContain("聊天工作台")
    expect(wrapper.text()).toContain("文档管理")
    expect(wrapper.text()).toContain("任务状态")
    expect(wrapper.text()).toContain("后端连接成功")
  })

  it("在健康检查失败时显示错误提示", async () => {
    mockFetchHealth.mockRejectedValue(new Error("无法连接后端服务。"))

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })

    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.text()).toContain("后端连接失败")
    expect(wrapper.text()).toContain("无法连接后端服务。")
  })
})
