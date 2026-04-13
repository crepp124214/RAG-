// 会话相关类型定义

export interface ChatSession {
  id: string
  title: string | null
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  citations: Citation[]
  tool_calls: ToolCall[]
  created_at: string
  updated_at: string
}

export interface Citation {
  document_id: string
  document_name: string
  chunk_id: string
  content: string
  page_number: number | null
  source_type: string
  asset_label: string | null
  preview_available: boolean
  relation_label?: string | null
  entity_path?: string | null
}

export interface ToolCall {
  tool_name: string
  arguments: Record<string, unknown>
  status: string
  result_summary: string | null
  error_code: string | null
  error_detail: string | null
}

export interface SessionUpdateParams {
  title?: string
  is_pinned?: boolean
}

export interface SessionSearchParams {
  search?: string
}

export interface SessionExportResult {
  content: string
}

export interface CreateSessionResult {
  session_id: string
  title: string
}
