import { API_BASE_URL } from "@/config/env"

export class ApiRequestError extends Error {
  code: string
  status: number

  constructor(message: string, options: { code: string; status: number }) {
    super(message)
    this.name = "ApiRequestError"
    this.code = options.code
    this.status = options.status
  }
}

export interface ApiErrorBody {
  code: string
  detail: string
}

export interface ApiEnvelope<T> {
  success: boolean
  message: string
  data: T | null
  error: ApiErrorBody | null
}

export function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}

export async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<ApiEnvelope<T>> {
  const headers = new Headers(init?.headers ?? {})
  const isFormData = typeof FormData !== "undefined" && init?.body instanceof FormData
  const method = init?.method?.toUpperCase() ?? "GET"

  if (!isFormData && method !== "GET" && method !== "HEAD" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(buildApiUrl(path), {
    headers,
    ...init,
  })

  let payload: ApiEnvelope<T> | null = null

  try {
    payload = (await response.json()) as ApiEnvelope<T>
  } catch {
    throw new ApiRequestError("服务返回了无法解析的响应。", {
      code: "INVALID_RESPONSE",
      status: response.status,
    })
  }

  if (!response.ok || !payload.success) {
    throw new ApiRequestError(
      payload.error?.detail ?? payload.message ?? "请求失败。",
      {
        code: payload.error?.code ?? "REQUEST_FAILED",
        status: response.status,
      },
    )
  }

  return payload
}
