import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { useDocumentStore } from "@/stores/documents"

const serviceMocks = vi.hoisted(() => ({
  fetchDocument: vi.fn(),
  fetchTask: vi.fn(),
  uploadDocument: vi.fn(),
  removeDocument: vi.fn(),
  fetchTags: vi.fn(),
  createTag: vi.fn(),
  updateTag: vi.fn(),
  deleteTag: vi.fn(),
  addDocumentTag: vi.fn(),
  removeDocumentTag: vi.fn(),
  setDocumentTags: vi.fn(),
  searchDocuments: vi.fn(),
  batchDeleteDocuments: vi.fn(),
  batchTagDocuments: vi.fn(),
  fetchDocumentPreview: vi.fn(),
}))

vi.mock("@/services/documents", async () => {
  const actual = await vi.importActual<typeof import("@/services/documents")>("@/services/documents")
  return {
    ...actual,
    fetchDocument: serviceMocks.fetchDocument,
    fetchTask: serviceMocks.fetchTask,
    uploadDocument: serviceMocks.uploadDocument,
    removeDocument: serviceMocks.removeDocument,
    fetchTags: serviceMocks.fetchTags,
    createTag: serviceMocks.createTag,
    updateTag: serviceMocks.updateTag,
    deleteTag: serviceMocks.deleteTag,
    addDocumentTag: serviceMocks.addDocumentTag,
    removeDocumentTag: serviceMocks.removeDocumentTag,
    setDocumentTags: serviceMocks.setDocumentTags,
    searchDocuments: serviceMocks.searchDocuments,
    batchDeleteDocuments: serviceMocks.batchDeleteDocuments,
    batchTagDocuments: serviceMocks.batchTagDocuments,
    fetchDocumentPreview: serviceMocks.fetchDocumentPreview,
  }
})

describe("useDocumentStore - 标签功能", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it("应该能够加载标签列表", async () => {
    const mockTags = [
      { id: 1, name: "重要", color: "#ff0000", created_at: "2026-04-01", updated_at: "2026-04-01" },
      { id: 2, name: "待处理", color: "#00ff00", created_at: "2026-04-02", updated_at: "2026-04-02" },
    ]
    serviceMocks.fetchTags.mockResolvedValue(mockTags)

    const store = useDocumentStore()
    await store.loadTags()

    expect(store.tags).toEqual(mockTags)
    expect(store.isLoadingTags).toBe(false)
  })

  it("应该能够创建新标签", async () => {
    const newTag = { id: 3, name: "新标签", color: "#0000ff", created_at: "2026-04-03", updated_at: "2026-04-03" }
    serviceMocks.createTag.mockResolvedValue(newTag)

    const store = useDocumentStore()
    await store.createNewTag("新标签", "#0000ff")

    expect(serviceMocks.createTag).toHaveBeenCalledWith("新标签", "#0000ff")
    expect(store.tags).toContainEqual(newTag)
  })

  it("应该能够更新标签", async () => {
    const updatedTag = { id: 1, name: "更新后", color: "#ff00ff", created_at: "2026-04-01", updated_at: "2026-04-03" }
    serviceMocks.updateTag.mockResolvedValue(updatedTag)

    const store = useDocumentStore()
    store.tags = [{ id: 1, name: "旧名称", color: "#ff0000", created_at: "2026-04-01", updated_at: "2026-04-01" }]

    await store.updateExistingTag(1, "更新后", "#ff00ff")

    expect(serviceMocks.updateTag).toHaveBeenCalledWith(1, "更新后", "#ff00ff")
    expect(store.tags[0].name).toBe("更新后")
  })

  it("应该能够删除标签", async () => {
    serviceMocks.deleteTag.mockResolvedValue(undefined)

    const store = useDocumentStore()
    store.tags = [{ id: 1, name: "待删除", color: "#ff0000", created_at: "2026-04-01", updated_at: "2026-04-01" }]

    await store.deleteExistingTag(1)

    expect(serviceMocks.deleteTag).toHaveBeenCalledWith(1)
    expect(store.tags).toHaveLength(0)
  })
})

describe("useDocumentStore - 搜索和筛选", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it("应该能够按关键词筛选文档", () => {
    const store = useDocumentStore()
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "测试文档.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-01",
        updatedAt: "2026-04-01",
        tags: [],
      },
      {
        documentId: "doc-2",
        taskId: "task-2",
        name: "开发手册.docx",
        fileType: "DOCX",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-02",
        updatedAt: "2026-04-02",
        tags: [],
      },
    ]

    store.searchKeyword = "测试"
    expect(store.filteredItems).toHaveLength(1)
    expect(store.filteredItems[0].name).toBe("测试文档.pdf")
  })

  it("应该能够按标签筛选文档", () => {
    const store = useDocumentStore()
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "文档1.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-01",
        updatedAt: "2026-04-01",
        tags: [{ id: 1, name: "重要", color: "#ff0000", created_at: "2026-04-01", updated_at: "2026-04-01" }],
      },
      {
        documentId: "doc-2",
        taskId: "task-2",
        name: "文档2.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-02",
        updatedAt: "2026-04-02",
        tags: [{ id: 2, name: "待处理", color: "#00ff00", created_at: "2026-04-02", updated_at: "2026-04-02" }],
      },
    ]

    store.selectedTags = [1]
    expect(store.filteredItems).toHaveLength(1)
    expect(store.filteredItems[0].name).toBe("文档1.pdf")
  })

  it("应该能够同时按关键词和标签筛选", () => {
    const store = useDocumentStore()
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "重要文档.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-01",
        updatedAt: "2026-04-01",
        tags: [{ id: 1, name: "重要", color: "#ff0000", created_at: "2026-04-01", updated_at: "2026-04-01" }],
      },
      {
        documentId: "doc-2",
        taskId: "task-2",
        name: "普通文档.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-02",
        updatedAt: "2026-04-02",
        tags: [{ id: 1, name: "重要", color: "#ff0000", created_at: "2026-04-01", updated_at: "2026-04-01" }],
      },
    ]

    store.searchKeyword = "重要"
    store.selectedTags = [1]
    expect(store.filteredItems).toHaveLength(1)
    expect(store.filteredItems[0].name).toBe("重要文档.pdf")
  })
})

describe("useDocumentStore - 批量操作", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it("应该能够选择和取消选择文档", () => {
    const store = useDocumentStore()

    store.toggleDocumentSelection("doc-1")
    expect(store.selectedDocuments.has("doc-1")).toBe(true)
    expect(store.hasSelectedDocuments).toBe(true)
    expect(store.selectedDocumentsCount).toBe(1)

    store.toggleDocumentSelection("doc-1")
    expect(store.selectedDocuments.has("doc-1")).toBe(false)
    expect(store.hasSelectedDocuments).toBe(false)
  })

  it("应该能够批量删除文档", async () => {
    serviceMocks.batchDeleteDocuments.mockResolvedValue(undefined)

    const store = useDocumentStore()
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "文档1.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-01",
        updatedAt: "2026-04-01",
        tags: [],
      },
      {
        documentId: "doc-2",
        taskId: "task-2",
        name: "文档2.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-02",
        updatedAt: "2026-04-02",
        tags: [],
      },
    ]
    store.selectedDocuments = new Set(["doc-1", "doc-2"])

    await store.batchDeleteSelectedDocuments()

    expect(serviceMocks.batchDeleteDocuments).toHaveBeenCalledWith(["doc-1", "doc-2"])
    expect(store.items).toHaveLength(0)
    expect(store.selectedDocuments.size).toBe(0)
  })

  it("应该能够批量打标签", async () => {
    serviceMocks.batchTagDocuments.mockResolvedValue(undefined)

    const store = useDocumentStore()
    store.tags = [{ id: 1, name: "重要", color: "#ff0000", created_at: "2026-04-01", updated_at: "2026-04-01" }]
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "文档1.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NOT_STARTED",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "document_processing",
        errorMessage: null,
        createdAt: "2026-04-01",
        updatedAt: "2026-04-01",
        tags: [],
      },
    ]
    store.selectedDocuments = new Set(["doc-1"])

    await store.batchTagSelectedDocuments([1])

    expect(serviceMocks.batchTagDocuments).toHaveBeenCalledWith(["doc-1"], [1])
  })

  it("应该能够清空选择", () => {
    const store = useDocumentStore()
    store.selectedDocuments = new Set(["doc-1", "doc-2", "doc-3"])

    store.clearDocumentSelection()

    expect(store.selectedDocuments.size).toBe(0)
    expect(store.hasSelectedDocuments).toBe(false)
  })
})

describe("useDocumentStore - 文档预览", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it("应该能够加载文档预览", async () => {
    const mockPreview = {
      document_id: "doc-1",
      document_name: "测试文档.pdf",
      chunks: [
        { id: 1, content: "第一段内容", chunk_index: 0, metadata: {} },
        { id: 2, content: "第二段内容", chunk_index: 1, metadata: {} },
      ],
      total_chunks: 10,
    }
    serviceMocks.fetchDocumentPreview.mockResolvedValue(mockPreview)

    const store = useDocumentStore()
    await store.loadDocumentPreview("doc-1")

    expect(store.previewData).toEqual(mockPreview)
    expect(store.isLoadingPreview).toBe(false)
  })

  it("应该能够清空预览数据", () => {
    const store = useDocumentStore()
    store.previewData = {
      document_id: "doc-1",
      document_name: "测试文档.pdf",
      chunks: [],
      total_chunks: 0,
    }

    store.clearDocumentPreview()

    expect(store.previewData).toBeNull()
  })
})
