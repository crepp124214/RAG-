import { requestJson } from "@/services/http"

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

export async function fetchTags(): Promise<Tag[]> {
  const response = await requestJson<Tag[]>("/api/tags")

  if (!response.data) {
    throw new Error("服务未返回标签列表。")
  }

  return response.data
}

export async function createTag(params: CreateTagParams): Promise<Tag> {
  const response = await requestJson<Tag>("/api/tags", {
    method: "POST",
    body: JSON.stringify(params),
  })

  if (!response.data) {
    throw new Error("创建标签成功，但服务未返回标签信息。")
  }

  return response.data
}

export async function updateTag(tagId: number, params: UpdateTagParams): Promise<Tag> {
  const response = await requestJson<Tag>(`/api/tags/${tagId}`, {
    method: "PUT",
    body: JSON.stringify(params),
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
