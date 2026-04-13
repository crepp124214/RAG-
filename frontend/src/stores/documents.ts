import { defineStore } from "pinia"

import {
  fetchDocument,
  fetchTask,
  removeDocument,
  uploadDocument,
  fetchTags,
  createTag,
  updateTag,
  deleteTag,
  addDocumentTag,
  removeDocumentTag,
  setDocumentTags,
  searchDocuments,
  batchDeleteDocuments,
  batchTagDocuments,
  fetchDocumentPreview,
  type DocumentDetailData,
  type TaskDetailData,
  type TagData,
  type DocumentSearchParams,
  type DocumentPreviewData,
} from "@/services/documents"
import { ApiRequestError } from "@/services/http"

const STORAGE_KEY = "rag-document-registry"
const TERMINAL_TASK_STATUSES = new Set(["READY", "FAILED"])
const TERMINAL_GRAPH_STATUSES = new Set(["READY", "FAILED"])
const pollingHandles = new Map<string, ReturnType<typeof setInterval>>()

interface PersistedDocumentEntry {
  documentId: string
  taskId: string
}

export interface DocumentListItem {
  documentId: string
  taskId: string
  name: string
  fileType: string
  documentStatus: string
  hasVisualAssets: boolean
  visualAssetCount: number
  hasGraph: boolean
  graphStatus: string
  graphRelationCount: number
  taskStatus: string
  taskType: string
  errorMessage: string | null
  createdAt: string
  updatedAt: string
  tags: TagData[]
}

interface DocumentState {
  items: DocumentListItem[]
  selectedDocumentId: string | null
  isUploading: boolean
  isHydrating: boolean
  uploadError: string | null
  actionError: string | null
  tags: TagData[]
  selectedTags: number[]
  searchKeyword: string
  selectedDocuments: Set<string>
  isLoadingTags: boolean
  previewData: DocumentPreviewData | null
  isLoadingPreview: boolean
}

function readRegistry(): PersistedDocumentEntry[] {
  if (typeof localStorage === "undefined") {
    return []
  }

  const raw = localStorage.getItem(STORAGE_KEY)
  if (!raw) {
    return []
  }

  try {
    return JSON.parse(raw) as PersistedDocumentEntry[]
  } catch {
    return []
  }
}

function writeRegistry(entries: PersistedDocumentEntry[]): void {
  if (typeof localStorage === "undefined") {
    return
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
}

function mergeDocumentDetail(
  entry: PersistedDocumentEntry,
  document: DocumentDetailData,
  task: TaskDetailData,
): DocumentListItem {
  return {
    documentId: entry.documentId,
    taskId: entry.taskId,
    name: document.name,
    fileType: document.file_type.toUpperCase(),
    documentStatus: document.status,
    hasVisualAssets: document.has_visual_assets,
    visualAssetCount: document.visual_asset_count,
    hasGraph: document.has_graph,
    graphStatus: document.graph_status,
    graphRelationCount: document.graph_relation_count,
    taskStatus: task.status,
    taskType: task.task_type,
    errorMessage: task.error_message,
    createdAt: document.created_at,
    updatedAt: task.updated_at ?? document.updated_at,
    tags: document.tags ?? [],
  }
}

function shouldContinuePolling(item: DocumentListItem): boolean {
  if (!TERMINAL_TASK_STATUSES.has(item.taskStatus)) {
    return true
  }

  return !TERMINAL_GRAPH_STATUSES.has(item.graphStatus)
}

export const useDocumentStore = defineStore("documents", {
  state: (): DocumentState => ({
    items: [],
    selectedDocumentId: null,
    isUploading: false,
    isHydrating: false,
    uploadError: null,
    actionError: null,
    tags: [],
    selectedTags: [],
    searchKeyword: "",
    selectedDocuments: new Set<string>(),
    isLoadingTags: false,
    previewData: null,
    isLoadingPreview: false,
  }),
  getters: {
    selectedItem(state): DocumentListItem | null {
      if (!state.selectedDocumentId) {
        return state.items[0] ?? null
      }

      return state.items.find((item) => item.documentId === state.selectedDocumentId) ?? null
    },
    trackedCount(state): number {
      return state.items.length
    },
    activeTaskCount(state): number {
      return state.items.filter((item) => !TERMINAL_TASK_STATUSES.has(item.taskStatus)).length
    },
    filteredItems(state): DocumentListItem[] {
      let filtered = state.items

      // Filter by search keyword
      if (state.searchKeyword) {
        const keyword = state.searchKeyword.toLowerCase()
        filtered = filtered.filter((item) => item.name.toLowerCase().includes(keyword))
      }

      // Filter by selected tags
      if (state.selectedTags.length > 0) {
        filtered = filtered.filter((item) =>
          state.selectedTags.some((tagId) => item.tags.some((tag) => tag.id === tagId)),
        )
      }

      return filtered
    },
    hasSelectedDocuments(state): boolean {
      return state.selectedDocuments.size > 0
    },
    selectedDocumentsCount(state): number {
      return state.selectedDocuments.size
    },
  },
  actions: {
    persistRegistry() {
      writeRegistry(
        this.items.map((item) => ({
          documentId: item.documentId,
          taskId: item.taskId,
        })),
      )
    },

    async loadTags() {
      this.isLoadingTags = true
      this.actionError = null

      try {
        this.tags = await fetchTags()
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "加载标签失败。"
      } finally {
        this.isLoadingTags = false
      }
    },

    async createNewTag(name: string, color: string) {
      this.actionError = null

      try {
        const tag = await createTag(name, color)
        this.tags.push(tag)
        return tag
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "创建标签失败。"
        throw error
      }
    },

    async updateExistingTag(tagId: number, name: string, color: string) {
      this.actionError = null

      try {
        const updatedTag = await updateTag(tagId, name, color)
        const index = this.tags.findIndex((tag) => tag.id === tagId)
        if (index >= 0) {
          this.tags.splice(index, 1, updatedTag)
        }
        return updatedTag
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "更新标签失败。"
        throw error
      }
    },

    async deleteExistingTag(tagId: number) {
      this.actionError = null

      try {
        await deleteTag(tagId)
        this.tags = this.tags.filter((tag) => tag.id !== tagId)
        this.selectedTags = this.selectedTags.filter((id) => id !== tagId)
        this.items = this.items.map((item) => ({
          ...item,
          tags: item.tags.filter((tag) => tag.id !== tagId),
        }))
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "删除标签失败。"
        throw error
      }
    },

    async addTagToDocument(documentId: string, tagId: number) {
      this.actionError = null

      try {
        await addDocumentTag(documentId, tagId)
        const document = this.items.find((item) => item.documentId === documentId)
        const tag = this.tags.find((item) => item.id === tagId)
        if (document && tag && !document.tags.some((item) => item.id === tagId)) {
          document.tags.push(tag)
        }
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "添加文档标签失败。"
        throw error
      }
    },

    async removeTagFromDocument(documentId: string, tagId: number) {
      this.actionError = null

      try {
        await removeDocumentTag(documentId, tagId)
        const document = this.items.find((item) => item.documentId === documentId)
        if (document) {
          document.tags = document.tags.filter((tag) => tag.id !== tagId)
        }
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "移除文档标签失败。"
        throw error
      }
    },

    async setTagsForDocument(documentId: string, tagIds: number[]) {
      this.actionError = null

      try {
        await setDocumentTags(documentId, tagIds)
        const document = this.items.find((item) => item.documentId === documentId)
        if (document) {
          document.tags = this.tags.filter((tag) => tagIds.includes(tag.id))
        }
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "设置文档标签失败。"
        throw error
      }
    },

    setSearchKeyword(keyword: string) {
      this.searchKeyword = keyword
    },

    setSelectedTags(tagIds: number[]) {
      this.selectedTags = tagIds
    },

    clearFilters() {
      this.searchKeyword = ""
      this.selectedTags = []
    },

    toggleDocumentSelection(documentId: string) {
      if (this.selectedDocuments.has(documentId)) {
        this.selectedDocuments.delete(documentId)
      } else {
        this.selectedDocuments.add(documentId)
      }
      this.selectedDocuments = new Set(this.selectedDocuments)
    },

    selectAllFilteredDocuments() {
      this.selectedDocuments = new Set(this.filteredItems.map((item) => item.documentId))
    },

    clearDocumentSelection() {
      this.selectedDocuments.clear()
      this.selectedDocuments = new Set()
    },

    async batchDeleteSelectedDocuments() {
      const documentIds = Array.from(this.selectedDocuments)
      if (documentIds.length === 0) {
        return
      }

      this.actionError = null

      try {
        await batchDeleteDocuments(documentIds)
        documentIds.forEach((documentId) => this.removeLocalItem(documentId))
        this.clearDocumentSelection()
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "批量删除文档失败。"
        throw error
      }
    },

    async batchTagSelectedDocuments(tagIds: number[]) {
      const documentIds = Array.from(this.selectedDocuments)
      if (documentIds.length === 0) {
        return
      }

      this.actionError = null

      try {
        await batchTagDocuments(documentIds, tagIds)
        const selectedTags = this.tags.filter((tag) => tagIds.includes(tag.id))
        this.items = this.items.map((item) => {
          if (documentIds.includes(item.documentId)) {
            return { ...item, tags: selectedTags }
          }
          return item
        })
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "批量设置标签失败。"
        throw error
      }
    },

    async loadDocumentPreview(documentId: string, limit: number = 5) {
      this.isLoadingPreview = true
      this.actionError = null

      try {
        this.previewData = await fetchDocumentPreview(documentId, limit)
        return this.previewData
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "加载文档预览失败。"
        throw error
      } finally {
        this.isLoadingPreview = false
      }
    },

    clearDocumentPreview() {
      this.previewData = null
    },

    async searchWithBackend(params: DocumentSearchParams) {
      this.actionError = null

      try {
        return await searchDocuments(params)
      } catch (error) {
        this.actionError = error instanceof Error ? error.message : "搜索文档失败。"
        throw error
      }
    },



    setSelectedDocument(documentId: string | null) {
      this.selectedDocumentId = documentId
    },

    upsertItem(item: DocumentListItem) {
      const existingIndex = this.items.findIndex(
        (current) => current.documentId === item.documentId,
      )

      if (existingIndex >= 0) {
        this.items.splice(existingIndex, 1, item)
      } else {
        this.items.unshift(item)
      }

      this.items.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))

      if (!this.selectedDocumentId) {
        this.selectedDocumentId = item.documentId
      }

      this.persistRegistry()
    },

    removeLocalItem(documentId: string) {
      this.items = this.items.filter((item) => item.documentId !== documentId)
      this.stopPolling(documentId)

      if (this.selectedDocumentId === documentId) {
        this.selectedDocumentId = this.items[0]?.documentId ?? null
      }

      this.persistRegistry()
    },

    startPolling(documentId: string) {
      if (pollingHandles.has(documentId)) {
        return
      }

      const handle = setInterval(() => {
        void this.refreshDocument(documentId)
      }, 2000)

      pollingHandles.set(documentId, handle)
    },

    stopPolling(documentId: string) {
      const handle = pollingHandles.get(documentId)
      if (!handle) {
        return
      }

      clearInterval(handle)
      pollingHandles.delete(documentId)
    },

    async hydrate() {
      this.isHydrating = true
      this.actionError = null

      const registry = readRegistry()
      const recovered: DocumentListItem[] = []

      for (const entry of registry) {
        try {
          const [document, task] = await Promise.all([
            fetchDocument(entry.documentId),
            fetchTask(entry.taskId),
          ])
          recovered.push(mergeDocumentDetail(entry, document, task))
        } catch (error) {
          if (
            !(error instanceof ApiRequestError) ||
            (error.code !== "document_not_found" && error.code !== "task_not_found")
          ) {
            this.actionError =
              error instanceof Error ? error.message : "恢复文档状态时发生未知错误。"
          }
        }
      }

      this.items = recovered.sort((left, right) => right.updatedAt.localeCompare(left.updatedAt))
      this.selectedDocumentId = this.items[0]?.documentId ?? null
      this.persistRegistry()

      for (const item of this.items) {
        if (shouldContinuePolling(item)) {
          this.startPolling(item.documentId)
        }
      }

      this.isHydrating = false
    },

    async refreshDocument(documentId: string) {
      const item = this.items.find((current) => current.documentId === documentId)
      if (!item) {
        return
      }

      try {
        const [document, task] = await Promise.all([
          fetchDocument(documentId),
          fetchTask(item.taskId),
        ])
        const merged = mergeDocumentDetail(
          { documentId: item.documentId, taskId: item.taskId },
          document,
          task,
        )
        this.upsertItem(merged)

        if (!shouldContinuePolling(merged)) {
          this.stopPolling(documentId)
        }
      } catch (error) {
        if (
          error instanceof ApiRequestError &&
          (error.code === "document_not_found" || error.code === "task_not_found")
        ) {
          this.removeLocalItem(documentId)
          return
        }

        this.actionError = error instanceof Error ? error.message : "刷新文档状态失败。"
      }
    },

    async upload(file: File) {
      this.isUploading = true
      this.uploadError = null
      this.actionError = null

      try {
        const payload = await uploadDocument(file)
        const entry = {
          documentId: payload.document_id,
          taskId: payload.task_id,
        }
        const [document, task] = await Promise.all([
          fetchDocument(entry.documentId),
          fetchTask(entry.taskId),
        ])

        this.upsertItem(mergeDocumentDetail(entry, document, task))
        this.startPolling(entry.documentId)
      } catch (error) {
        this.uploadError = error instanceof Error ? error.message : "上传文档失败。"
        throw error
      } finally {
        this.isUploading = false
      }
    },

    async deleteDocument(documentId: string) {
      this.actionError = null

      try {
        await removeDocument(documentId)
        this.removeLocalItem(documentId)
      } catch (error) {
        if (error instanceof ApiRequestError && error.code === "document_not_found") {
          this.removeLocalItem(documentId)
          return
        }

        this.actionError = error instanceof Error ? error.message : "删除文档失败。"
        throw error
      }
    },
  },
})
