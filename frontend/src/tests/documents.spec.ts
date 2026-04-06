import { createPinia, setActivePinia } from "pinia"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { useDocumentStore } from "@/stores/documents"

const serviceMocks = vi.hoisted(() => ({
  uploadDocument: vi.fn(),
  fetchDocument: vi.fn(),
  fetchTask: vi.fn(),
  removeDocument: vi.fn(),
}))

vi.mock("@/services/documents", () => ({
  uploadDocument: serviceMocks.uploadDocument,
  fetchDocument: serviceMocks.fetchDocument,
  fetchTask: serviceMocks.fetchTask,
  removeDocument: serviceMocks.removeDocument,
}))

describe("useDocumentStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it("能从本地记录恢复文档和任务状态", async () => {
    localStorage.setItem(
      "rag-document-registry",
      JSON.stringify([{ documentId: "doc-1", taskId: "task-1" }]),
    )

    serviceMocks.fetchDocument.mockResolvedValue({
      id: "doc-1",
      name: "研发周报.pdf",
      file_type: "pdf",
      status: "READY",
      storage_path: "/tmp/doc-1",
      has_visual_assets: true,
      visual_asset_count: 2,
      has_graph: true,
      graph_status: "READY",
      graph_relation_count: 8,
      created_at: "2026-04-04T09:00:00",
      updated_at: "2026-04-04T09:10:00",
    })
    serviceMocks.fetchTask.mockResolvedValue({
      id: "task-1",
      document_id: "doc-1",
      task_type: "INGESTION",
      status: "READY",
      error_message: null,
      created_at: "2026-04-04T09:00:00",
      updated_at: "2026-04-04T09:10:00",
    })

    const store = useDocumentStore()
    await store.hydrate()

    expect(store.items).toHaveLength(1)
    expect(store.items[0].name).toBe("研发周报.pdf")
    expect(store.items[0].taskStatus).toBe("READY")
    expect(store.items[0].visualAssetCount).toBe(2)
    expect(store.items[0].hasGraph).toBe(true)
    expect(store.items[0].graphStatus).toBe("READY")
    expect(store.items[0].graphRelationCount).toBe(8)
    expect(store.selectedDocumentId).toBe("doc-1")
  })

  it("上传成功后会记录文档并写入本地注册表", async () => {
    serviceMocks.uploadDocument.mockResolvedValue({
      document_id: "doc-2",
      task_id: "task-2",
    })
    serviceMocks.fetchDocument.mockResolvedValue({
      id: "doc-2",
      name: "notes.txt",
      file_type: "txt",
      status: "UPLOADED",
      storage_path: "/tmp/doc-2",
      has_visual_assets: false,
      visual_asset_count: 0,
      has_graph: false,
      graph_status: "NOT_STARTED",
      graph_relation_count: 0,
      created_at: "2026-04-04T09:00:00",
      updated_at: "2026-04-04T09:00:00",
    })
    serviceMocks.fetchTask.mockResolvedValue({
      id: "task-2",
      document_id: "doc-2",
      task_type: "INGESTION",
      status: "UPLOADED",
      error_message: null,
      created_at: "2026-04-04T09:00:00",
      updated_at: "2026-04-04T09:00:00",
    })

    const store = useDocumentStore()
    await store.upload(new File(["hello"], "notes.txt", { type: "text/plain" }))

    expect(store.items).toHaveLength(1)
    expect(JSON.parse(localStorage.getItem("rag-document-registry") ?? "[]")).toEqual([
      { documentId: "doc-2", taskId: "task-2" },
    ])
  })

  it("删除成功后会移除本地文档记录", async () => {
    const store = useDocumentStore()
    store.items = [
      {
        documentId: "doc-3",
        taskId: "task-3",
        name: "manual.docx",
        fileType: "DOCX",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "FAILED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-04T09:00:00",
        updatedAt: "2026-04-04T09:00:00",
      },
    ]
    store.selectedDocumentId = "doc-3"
    store.persistRegistry()

    await store.deleteDocument("doc-3")

    expect(store.items).toHaveLength(0)
    expect(localStorage.getItem("rag-document-registry")).toBe("[]")
  })

  it("入库任务完成但图谱仍在处理时会继续轮询文档详情", async () => {
    vi.useFakeTimers()
    const store = useDocumentStore()
    store.items = [
      {
        documentId: "doc-graph",
        taskId: "task-ingestion",
        name: "graph.txt",
        fileType: "TXT",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "PROCESSING",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-06T09:00:00",
        updatedAt: "2026-04-06T09:01:00",
      },
    ]

    serviceMocks.fetchDocument.mockResolvedValue({
      id: "doc-graph",
      name: "graph.txt",
      file_type: "txt",
      status: "READY",
      storage_path: "/tmp/doc-graph",
      has_visual_assets: false,
      visual_asset_count: 0,
      has_graph: false,
      graph_status: "PROCESSING",
      graph_relation_count: 0,
      created_at: "2026-04-06T09:00:00",
      updated_at: "2026-04-06T09:02:00",
    })
    serviceMocks.fetchTask.mockResolvedValue({
      id: "task-ingestion",
      document_id: "doc-graph",
      task_type: "INGESTION",
      status: "READY",
      error_message: null,
      created_at: "2026-04-06T09:00:00",
      updated_at: "2026-04-06T09:02:00",
    })

    store.startPolling("doc-graph")
    await store.refreshDocument("doc-graph")
    await vi.advanceTimersByTimeAsync(2000)

    expect(serviceMocks.fetchDocument).toHaveBeenCalledTimes(2)
  })
})
