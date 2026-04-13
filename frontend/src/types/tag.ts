// 标签相关类型定义

export interface Tag {
  id: number
  name: string
  color: string
  created_at: string
  updated_at: string
}

export interface CreateTagParams {
  name: string
  color: string
}

export interface UpdateTagParams {
  name: string
  color: string
}

export interface DocumentTag {
  document_id: string
  tag_id: number
}

export interface BatchTagParams {
  document_ids: string[]
  tag_ids: number[]
}
