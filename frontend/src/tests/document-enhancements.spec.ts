import { createPinia, setActivePinia } from "pinia"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { useDocumentStore } from "@/stores/documents"
import type { TagData } from "@/services/documents"

const serviceMocks = vi.hoisted(() => ({
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
  fetchDocument: vi.fn(),
  fetchTask: vi.fn(),
}))

vi.mock("@/services/documents", async () => {
  const actual = await vi.importActual("@/services/documents")
  return {
    ...actual,
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
    fetchDocument: serviceMocks.fetchDocument,
    fetchTask: serviceMocks.fetchTask,
  }
})

describe("Document Store - Tag Management", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("能加载标签列表", async () => {
    const mockTags: TagData[] = [
      { id: 1, name: "重要", color: "#F56C6C", created_at: "2026-04-13T10:00:00", updated_at: "2026-04-13T10:00:00" },
      { id: 2, name: "技术", color: "#409EFF", created_at: "2026-04-13T10:01:00", updated_at: "2026-04-13T10:01:00" },
    ]
    serviceMocks.fetchTags.mockResolvedValue(mockTags)

    const store = useDocumentStore()
    await store.loadTags()

    expect(store.tags).toHaveLength(2)
    expect(store.tags[0].name).toBe("重要")
    expect(store.tags[1].name).toBe("技术")
  })

  it("能创建新标签", async () => {
    const newTag: TagData = {
      id: 3,
      name: "紧急",
      color: "#E6A23C",
      created_at: "2026-04-13T10:05:00",
      updated_at: "2026-04-13T10:05:00",
    }
    serviceMocks.createTag.mockResolvedValue(newTag)

    const store = useDocumentStore()
    await store.createNewTag("紧急", "#E6A23C")

    expect(store.tags).toHaveLength(1)
    expect(store.tags[0].name).toBe("紧急")
  })

  it("能更新标签", async () => {
    const store = useDocumentStore()
    store.tags = [
      { id: 1, name: "重要", color: "#F56C6C", created_at: "2026-04-13T10:00:00", updated_at: "2026-04-13T10:00:00" },
    ]

    const updatedTag: TagData = {
      id: 1,
      name: "非常重要",
      color: "#FF0000",
      created_at: "2026-04-13T10:00:00",
      updated_at: "2026-04-13T10:10:00",
    }
    serviceMocks.updateTag.mockResolvedValue(updatedTag)

    await store.updateExistingTag(1, "非常重要", "#FF0000")

    expect(store.tags[0].name).toBe("非常重要")
    expect(store.tags[0].color).toBe("#FF0000")
  })

  it("删除标签时会自动移除文档关联", async () => {
    const store = useDocumentStore()
    store.tags = [
      { id: 1, name: "重要", color: "#F56C6C", created_at: "2026-04-13T10:00:00", updated_at: "2026-04-13T10:00:00" },
      { id: 2, name: "技术", color: "#409EFF", created_at: "2026-04-13T10:01:00", updated_at: "2026-04-13T10:01:00" },
    ]
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "test.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
        tags: [store.tags[0], store.tags[1]],
      },
    ]

    serviceMocks.deleteTag.mockResolvedValue(undefined)

    await store.deleteExistingTag(1)

    expect(store.tags).toHaveLength(1)
    expect(store.tags[0].id).toBe(2)
    expect(store.items[0].tags).toHaveLength(1)
    expect(store.items[0].tags[0].id).toBe(2)
  })

  it("能给文档添加标签", async () => {
    const store = useDocumentStore()
    store.tags = [
      { id: 1, name: "重要", color: "#F56C6C", created_at: "2026-04-13T10:00:00", updated_at: "2026-04-13T10:00:00" },
    ]
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "test.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
        tags: [],
      },
    ]

    serviceMocks.addDocumentTag.mockResolvedValue(undefined)

    await store.addTagToDocument("doc-1", 1)

    expect(store.items[0].tags).toHaveLength(1)
    expect(store.items[0].tags[0].name).toBe("重要")
  })

  it("能移除文档标签", async () => {
    const store = useDocumentStore()
    store.tags = [
      { id: 1, name: "重要", color: "#F56C6C", created_at: "2026-04-13T10:00:00", updated_at: "2026-04-13T10:00:00" },
    ]
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "test.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
        tags: [store.tags[0]],
      },
    ]

    serviceMocks.removeDocumentTag.mockResolvedValue(undefined)

    await store.removeTagFromDocument("doc-1", 1)

    expect(store.items[0].tags).toHaveLength(0)
  })
})

describe("Document Store - Search and Filter", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("能按关键词筛选文档", () => {
    const store = useDocumentStore()
    store.items = [
      {
        documentId: "doc-1",
        taskId: "task-1",
        name: "技术文档.pdf",
        fileType: "PDF",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
        tags: [],
      },
      {
        documentId: "doc-2",
        taskId: "task-2",
        name: "产品需求.docx",
        fileType: "DOCX",
        documentStatus: "READY",
        hasVisualAssets: false,
        visualAssetCount: 0,
        hasGraph: false,
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:01:00",
        updatedAt: "2026-04-13T10:01:00",
        tags: [],
      },
    ]

    store.setSearchKeyword("技术")

    expect(store.filteredItems).toHaveLength(1)
    expect(store.filteredItems[0].name).toBe("技术文档.pdf")
  })

  it("能按标签筛选文档", () => {
    const store = useDocumentStore()
    const tag1: TagData = { id: 1, name: "重要", color: "#F56C6C", created_at: "2026-04-13T10:00:00", updated_at: "2026-04-13T10:00:00" }
    const tag2: TagData = { id: 2, name: "技术", color: "#409EFF", created_at: "2026-04-13T10:01:00", updated_at: "2026-04-13T10:01:00" }

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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
        tags: [tag1],
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:01:00",
        updatedAt: "2026-04-13T10:01:00",
        tags: [tag2],
      },
    ]

    store.setSelectedTags([1])

    expect(store.filteredItems).toHaveLength(1)
    expect(store.filteredItems[0].name).toBe("文档1.pdf")
  })

  it("能清除所有筛选条件", () => {
    const store = useDocumentStore()
    store.searchKeyword = "测试"
    store.selectedTags = [1, 2]

    store.clearFilters()

    expect(store.searchKeyword).toBe("")
    expect(store.selectedTags).toHaveLength(0)
  })
})

describe("Document Store - Batch Operations", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("能批量选择文档", () => {
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:01:00",
        updatedAt: "2026-04-13T10:01:00",
        tags: [],
      },
    ]

    store.toggleDocumentSelection("doc-1")
    store.toggleDocumentSelection("doc-2")

    expect(store.hasSelectedDocuments).toBe(true)
    expect(store.selectedDocumentsCount).toBe(2)
  })

  it("能全选筛选后的文档", () => {
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:01:00",
        updatedAt: "2026-04-13T10:01:00",
        tags: [],
      },
    ]

    store.selectAllFilteredDocuments()

    expect(store.selectedDocumentsCount).toBe(2)
  })

  it("能批量删除选中的文档", async () => {
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:01:00",
        updatedAt: "2026-04-13T10:01:00",
        tags: [],
      },
    ]
    store.selectedDocuments = new Set(["doc-1", "doc-2"])

    serviceMocks.batchDeleteDocuments.mockResolvedValue(undefined)

    await store.batchDeleteSelectedDocuments()

    expect(store.items).toHaveLength(0)
    expect(store.selectedDocumentsCount).toBe(0)
  })

  it("能批量设置标签", async () => {
    const store = useDocumentStore()
    const tag1: TagData = { id: 1, name: "重要", color: "#F56C6C", created_at: "2026-04-13T10:00:00", updated_at: "2026-04-13T10:00:00" }
    store.tags = [tag1]
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:00:00",
        updatedAt: "2026-04-13T10:00:00",
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
        graphStatus: "NONE",
        graphRelationCount: 0,
        taskStatus: "READY",
        taskType: "INGESTION",
        errorMessage: null,
        createdAt: "2026-04-13T10:01:00",
        updatedAt: "2026-04-13T10:01:00",
        tags: [],
      },
    ]
    store.selectedDocuments = new Set(["doc-1", "doc-2"])

    serviceMocks.batchTagDocuments.mockResolvedValue(undefined)

    await store.batchTagSelectedDocuments([1])

    expect(store.items[0].tags).toHaveLength(1)
    expect(store.items[0].tags[0].name).toBe("重要")
    expect(store.items[1].tags).toHaveLength(1)
    expect(store.items[1].tags[0].name).toBe("重要")
  })
})

describe("Document Store - Preview", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it("能加载文档预览", async () => {
    const store = useDocumentStore()
    const mockPreview = {
      document_id: "doc-1",
      document_name: "test.pdf",
      chunks: [
        { id: 1, content: "第一段内容", chunk_index: 0, metadata: {} },
        { id: 2, content: "第二段内容", chunk_index: 1, metadata: {} },
      ],
      total_chunks: 10,
    }

    serviceMocks.fetchDocumentPreview.mockResolvedValue(mockPreview)

    await store.loadDocumentPreview("doc-1")

    expect(store.previewData).not.toBeNull()
    expect(store.previewData?.chunks).toHaveLength(2)
    expect(store.previewData?.total_chunks).toBe(10)
  })

  it("能清除文档预览", () => {
    const store = useDocumentStore()
    store.previewData = {
      document_id: "doc-1",
      document_name: "test.pdf",
      chunks: [],
      total_chunks: 0,
    }

    store.clearDocumentPreview()

    expect(store.previewData).toBeNull()
  })
})
