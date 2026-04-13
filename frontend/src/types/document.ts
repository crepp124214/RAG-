// 文档相关类型定义

export interface Document {
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

export interface DocumentWithTags extends Document {
  tags: Array<{
    id: number
    name: string
    color: string
  }>
}

export interface DocumentSearchParams {
  search?: string
  tags?: number[]
  sort?: string
  order?: 'asc' | 'desc'
}

export interface DocumentChunk {
  id: number
  content: string
  chunk_index: number
  metadata: Record<string, unknown>
}

export interface DocumentPreview {
  document_id: string
  document_name: string
  chunks: DocumentChunk[]
  total_chunks: number
}

export interface BatchDeleteParams {
  document_ids: string[]
}

export interface UploadResult {
  document_id: string
  task_id: string
}

export interface Task {
  id: string
  document_id: string
  task_type: string
  status: string
  error_message: string | null
  created_at: string
  updated_at: string
}
