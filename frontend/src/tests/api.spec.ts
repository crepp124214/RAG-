import { describe, expect, it, vi } from "vitest"

import { uploadDocument } from "@/services/documents"
import { requestJson } from "@/services/http"
import { fetchHealth } from "@/services/system"

describe("requestJson", () => {
  it("在成功响应时返回标准数据结构", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: "ok",
          data: { value: "ready" },
          error: null,
        }),
      }),
    )

    const payload = await requestJson<{ value: string }>("/api/health")

    expect(payload.data).toEqual({ value: "ready" })
  })

  it("GET 请求不会附加 JSON Content-Type，避免无必要的预检", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        message: "ok",
        data: { value: "ready" },
        error: null,
      }),
    })

    vi.stubGlobal("fetch", fetchMock)

    await requestJson<{ value: string }>("/api/health")

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = new Headers(init.headers)

    expect(headers.has("Content-Type")).toBe(false)
  })

  it("在接口返回标准错误时抛出可读异常", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({
          success: false,
          message: "request failed",
          data: null,
          error: {
            code: "SERVICE_UNAVAILABLE",
            detail: "后端服务暂不可用",
          },
        }),
      }),
    )

    await expect(requestJson("/api/health")).rejects.toMatchObject({
      message: "后端服务暂不可用",
      code: "SERVICE_UNAVAILABLE",
      status: 503,
    })
  })

  it("上传 FormData 时不会强行附加 JSON Content-Type", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        message: "ok",
        data: {
          document_id: "doc-1",
          task_id: "task-1",
        },
        error: null,
      }),
    })

    vi.stubGlobal("fetch", fetchMock)

    await uploadDocument(new File(["hello"], "demo.txt", { type: "text/plain" }))

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    const headers = new Headers(init.headers)

    expect(init.body).toBeInstanceOf(FormData)
    expect(headers.has("Content-Type")).toBe(false)
  })
})

describe("fetchHealth", () => {
  it("能提取健康检查 payload", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          success: true,
          message: "服务运行正常",
          data: {
            status: "ok",
            app_name: "rag-system",
            app_env: "development",
          },
          error: null,
        }),
      }),
    )

    await expect(fetchHealth()).resolves.toEqual({
      status: "ok",
      app_name: "rag-system",
      app_env: "development",
    })
  })
})
