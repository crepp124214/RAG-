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
