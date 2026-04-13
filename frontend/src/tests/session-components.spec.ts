import { mount } from "@vue/test-utils"
import { describe, expect, it } from "vitest"
import ElementPlus from "element-plus"

import SessionSearchBar from "@/components/chat/SessionSearchBar.vue"
import SessionRenameDialog from "@/components/chat/SessionRenameDialog.vue"
import SessionExportDialog from "@/components/chat/SessionExportDialog.vue"

describe("SessionSearchBar", () => {
  it("应该渲染搜索输入框", () => {
    const wrapper = mount(SessionSearchBar, {
      props: {
        modelValue: "",
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.find(".session-search-bar").exists()).toBe(true)
  })

  it("应该在输入时触发 search 事件", async () => {
    const wrapper = mount(SessionSearchBar, {
      props: {
        modelValue: "",
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    const input = wrapper.findComponent({ name: "ElInput" })
    await input.vm.$emit("input", "测试关键词")

    expect(wrapper.emitted("search")).toBeTruthy()
    expect(wrapper.emitted("search")?.[0]).toEqual(["测试关键词"])
  })
})

describe("SessionRenameDialog", () => {
  it("应该接收正确的 props", () => {
    const wrapper = mount(SessionRenameDialog, {
      props: {
        visible: true,
        sessionId: "session-1",
        currentTitle: "旧标题",
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.props("visible")).toBe(true)
    expect(wrapper.props("sessionId")).toBe("session-1")
    expect(wrapper.props("currentTitle")).toBe("旧标题")
  })

  it("应该能够触发 confirm 事件", async () => {
    const wrapper = mount(SessionRenameDialog, {
      props: {
        visible: true,
        sessionId: "session-1",
        currentTitle: "旧标题",
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    await wrapper.vm.$emit("confirm", "session-1", "新标题")

    expect(wrapper.emitted("confirm")).toBeTruthy()
    expect(wrapper.emitted("confirm")?.[0]).toEqual(["session-1", "新标题"])
  })
})

describe("SessionExportDialog", () => {
  it("应该接收正确的 props", () => {
    const wrapper = mount(SessionExportDialog, {
      props: {
        visible: true,
        sessionId: "session-1",
        sessionTitle: "测试会话",
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    expect(wrapper.props("visible")).toBe(true)
    expect(wrapper.props("sessionId")).toBe("session-1")
    expect(wrapper.props("sessionTitle")).toBe("测试会话")
  })

  it("应该能够触发 export 事件", async () => {
    const wrapper = mount(SessionExportDialog, {
      props: {
        visible: true,
        sessionId: "session-1",
        sessionTitle: "测试会话",
      },
      global: {
        plugins: [ElementPlus],
      },
    })

    await wrapper.vm.$emit("export", "session-1")

    expect(wrapper.emitted("export")).toBeTruthy()
    expect(wrapper.emitted("export")?.[0]).toEqual(["session-1"])
  })
})
