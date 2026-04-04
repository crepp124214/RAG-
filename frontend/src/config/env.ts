export interface FrontendEnvSource {
  VITE_API_BASE_URL?: string
}

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"

export function resolveApiBaseUrl(
  source: FrontendEnvSource = import.meta.env as FrontendEnvSource,
): string {
  const rawValue = source.VITE_API_BASE_URL?.trim()
  if (!rawValue) {
    return DEFAULT_API_BASE_URL
  }

  return rawValue.replace(/\/+$/, "")
}

export const API_BASE_URL = resolveApiBaseUrl()
