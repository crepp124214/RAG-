import { defineStore } from "pinia"

import {
  fetchDocument,
  fetchTask,
  removeDocument,
  uploadDocument,
  type DocumentDetailData,
  type TaskDetailData,
} from "@/services/documents"
import { ApiRequestError } from "@/services/http"

const STORAGE_KEY = "rag-document-registry"
const TERMINAL_TASK_STATUSES = new Set(["READY", "FAILED"])
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
  taskStatus: string
  taskType: string
  errorMessage: string | null
  createdAt: string
  updatedAt: string
}

interface DocumentState {
  items: DocumentListItem[]
  selectedDocumentId: string | null
  isUploading: boolean
  isHydrating: boolean
  uploadError: string | null
  actionError: string | null
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
    taskStatus: task.status,
    taskType: task.task_type,
    errorMessage: task.error_message,
    createdAt: document.created_at,
    updatedAt: task.updated_at ?? document.updated_at,
  }
}

export const useDocumentStore = defineStore("documents", {
  state: (): DocumentState => ({
    items: [],
    selectedDocumentId: null,
    isUploading: false,
    isHydrating: false,
    uploadError: null,
    actionError: null,
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
        if (!TERMINAL_TASK_STATUSES.has(item.taskStatus)) {
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

        if (TERMINAL_TASK_STATUSES.has(merged.taskStatus)) {
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
