import { requestJson } from "@/services/http"

export interface HealthPayload {
  status: string
  app_name: string
  app_env: string
}

export async function fetchHealth(): Promise<HealthPayload> {
  const response = await requestJson<HealthPayload>("/api/health")
  if (!response.data) {
    throw new Error("健康检查未返回 data。")
  }

  return response.data
}
