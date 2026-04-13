import { requestJson } from "@/services/http"

export interface UploadDocumentData {
  document_id: string
  task_id: string
}

export interface DocumentDetailData {
  id: string
  name: string
  file_type: string
  status: string
  storage_path: string
  has_visual_assets: boolean
  visual_asset_count: number
  has_graph: boolean
  graph_status: string
  graph_relation_count: number
  created_at: string
  updated_at: string
  tags?: TagData[]
}

export interface TaskDetailData {
  id: string
  document_id: string
  task_type: string
  status: string
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface TagData {
  id: number
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface DocumentChunkData {
  id: number
  content: string
  chunk_index: number
  metadata: Record<string, unknown>
}

export interface DocumentPreviewData {
  document_id: string
  document_name: string
  chunks: DocumentChunkData[]
  total_chunks: number
}

export async function uploadDocument(file: File): Promise<UploadDocumentData> {
  const formData = new FormData()
  formData.append("file", file)

  const response = await requestJson<UploadDocumentData>("/api/documents/upload", {
    method: "POST",
    body: formData,
  })

  if (!response.data) {
    throw new Error("文档上传成功，但服务未返回文档信息。")
  }

  return response.data
}

export async function fetchDocument(documentId: string): Promise<DocumentDetailData> {
  const response = await requestJson<DocumentDetailData>(`/api/documents/${documentId}`)

  if (!response.data) {
    throw new Error("服务未返回文档详情。")
  }

  return response.data
}

export async function fetchTask(taskId: string): Promise<TaskDetailData> {
  const response = await requestJson<TaskDetailData>(`/api/tasks/${taskId}`)

  if (!response.data) {
    throw new Error("服务未返回任务详情。")
  }

  return response.data
}

export async function removeDocument(documentId: string): Promise<void> {
  await requestJson<null>(`/api/documents/${documentId}`, {
    method: "DELETE",
  })
}

// Tag Management
export async function fetchTags(): Promise<TagData[]> {
  const response = await requestJson<TagData[]>("/api/tags")

  if (!response.data) {
    throw new Error("服务未返回标签列表。")
  }

  return response.data
}

export async function createTag(name: string, color: string): Promise<TagData> {
  const response = await requestJson<TagData>("/api/tags", {
    method: "POST",
    body: JSON.stringify({ name, color }),
  })

  if (!response.data) {
    throw new Error("创建标签成功，但服务未返回标签信息。")
  }

  return response.data
}

export async function updateTag(tagId: number, name: string, color: string): Promise<TagData> {
  const response = await requestJson<TagData>(`/api/tags/${tagId}`, {
    method: "PUT",
    body: JSON.stringify({ name, color }),
  })

  if (!response.data) {
    throw new Error("更新标签成功，但服务未返回标签信息。")
  }

  return response.data
}

export async function deleteTag(tagId: number): Promise<void> {
  await requestJson<null>(`/api/tags/${tagId}`, {
    method: "DELETE",
  })
}

// Document Tag Relations
export async function addDocumentTag(documentId: string, tagId: number): Promise<void> {
  await requestJson<null>(`/api/documents/${documentId}/tags`, {
    method: "POST",
    body: JSON.stringify({ tag_id: tagId }),
  })
}

export async function removeDocumentTag(documentId: string, tagId: number): Promise<void> {
  await requestJson<null>(`/api/documents/${documentId}/tags/${tagId}`, {
    method: "DELETE",
  })
}

export async function setDocumentTags(documentId: string, tagIds: number[]): Promise<void> {
  await requestJson<null>(`/api/documents/${documentId}/tags`, {
    method: "PUT",
    body: JSON.stringify({ tag_ids: tagIds }),
  })
}

// Document Search and Filter
export interface DocumentSearchParams {
  search?: string
  tags?: number[]
  sort?: string
  order?: "asc" | "desc"
}

export async function searchDocuments(
  params: DocumentSearchParams,
): Promise<DocumentDetailData[]> {
  const queryParams = new URLSearchParams()

  if (params.search) {
    queryParams.append("search", params.search)
  }

  if (params.tags && params.tags.length > 0) {
    queryParams.append("tags", params.tags.join(","))
  }

  if (params.sort) {
    queryParams.append("sort", params.sort)
  }

  if (params.order) {
    queryParams.append("order", params.order)
  }

  const response = await requestJson<DocumentDetailData[]>(
    `/api/documents?${queryParams.toString()}`,
  )

  if (!response.data) {
    throw new Error("服务未返回文档列表。")
  }

  return response.data
}

// Batch Operations
export async function batchDeleteDocuments(documentIds: string[]): Promise<void> {
  await requestJson<null>("/api/documents/batch-delete", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds }),
  })
}

export async function batchTagDocuments(documentIds: string[], tagIds: number[]): Promise<void> {
  await requestJson<null>("/api/documents/batch-tag", {
    method: "POST",
    body: JSON.stringify({ document_ids: documentIds, tag_ids: tagIds }),
  })
}

// Document Preview
export async function fetchDocumentPreview(
  documentId: string,
  limit: number = 5,
): Promise<DocumentPreviewData> {
  const response = await requestJson<DocumentPreviewData>(
    `/api/documents/${documentId}/preview?limit=${limit}`,
  )

  if (!response.data) {
    throw new Error("服务未返回文档预览。")
  }

  return response.data
}
