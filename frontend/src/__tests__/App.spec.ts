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

  it("渲染桌面化研究工作台壳层，并在左侧保留紧凑的会话导航 rail", async () => {
    mockFetchHealth.mockResolvedValue({
      status: "ok",
      app_name: "rag-system",
      app_env: "development",
    })

    const wrapper = mount(App, {
      global: {
        plugins: [createPinia(), ElementPlus],
        stubs: {
          SessionSidebar: {
            template: `
              <nav aria-label="会话导航">
                <button type="button">新建</button>
                <span>快速切换</span>
              </nav>
            `,
          },
          ChatWorkspacePanel: { template: "<div>聊天工作台区域</div>" },
          DocumentManagerPanel: { template: "<div>文档管理区域</div>" },
          TaskStatusPanel: { template: "<div>任务状态区域</div>" },
        },
      },
    })

    await Promise.resolve()
    await Promise.resolve()

    expect(wrapper.findAll("aside")).toHaveLength(2)
    expect(wrapper.find("main").exists()).toBe(true)
    expect(wrapper.find("header").exists()).toBe(true)
    expect(wrapper.find("main").text()).toContain("服务状态：ok，环境：development")
    expect(wrapper.find("aside.nav-rail").exists()).toBe(true)
    expect(wrapper.find("aside.nav-rail").text()).toContain("快速切换")
    expect(wrapper.find('[aria-label="会话导航"]').exists()).toBe(true)
    expect(wrapper.text()).toContain("研究工作区")
    expect(wrapper.text()).toContain("证据与任务")
    expect(wrapper.text()).toContain("新建")
    expect(wrapper.text()).toContain("聊天工作台区域")
    expect(wrapper.text()).toContain("文档管理区域")
    expect(wrapper.text()).toContain("任务状态区域")
  })

  it("在健康检查进行中时显示更明显的状态提示", async () => {
    mockFetchHealth.mockImplementation(() => new Promise(() => {}))

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

    expect(wrapper.text()).toContain("正在检查后端健康状态")
    expect(wrapper.text()).toContain("正在请求 /api/health 验证前后端联通情况。")
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
    expect(wrapper.text()).toContain("请先恢复后端服务后再继续当前研究流程。")
  })
})
