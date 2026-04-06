import { ApiRequestError, buildApiUrl, requestJson } from "@/services/http"

export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: string
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

export interface CreateSessionData {
  session_id: string
  title: string
}

export interface ChatQueryData {
  answer: string
  citations: Citation[]
  tool_calls: ToolCall[]
  user_message_id: string
  assistant_message_id: string
}

export interface ChatStreamStartEvent {
  event: "message_start"
  data: { session_id: string }
}

export interface ChatStreamTokenEvent {
  event: "token"
  data: { content: string }
}

export interface ChatStreamToolCallEvent {
  event: "tool_call"
  data: {
    tool_name: string
    arguments: Record<string, unknown>
  }
}

export interface ChatStreamToolResultEvent {
  event: "tool_result"
  data: ToolCall
}

export interface ChatStreamCitationEvent {
  event: "citation"
  data: Citation
}

export interface ChatStreamEndEvent {
  event: "message_end"
  data: {
    answer: string
    citations: Citation[]
    tool_calls: ToolCall[]
    user_message_id: string
    assistant_message_id: string
    session_id: string
  }
}

export interface ChatStreamErrorEvent {
  event: "error"
  data: {
    code: string
    detail: string
  }
}

export type ChatStreamEvent =
  | ChatStreamStartEvent
  | ChatStreamToolCallEvent
  | ChatStreamToolResultEvent
  | ChatStreamTokenEvent
  | ChatStreamCitationEvent
  | ChatStreamEndEvent
  | ChatStreamErrorEvent

export async function createSession(): Promise<CreateSessionData> {
  const response = await requestJson<CreateSessionData>("/api/chat/sessions", {
    method: "POST",
  })

  if (!response.data) {
    throw new Error("服务未返回会话信息。")
  }

  return response.data
}

export async function fetchSessions(): Promise<ChatSession[]> {
  const response = await requestJson<ChatSession[]>("/api/chat/sessions")
  return response.data ?? []
}

export async function fetchMessages(sessionId: string): Promise<ChatMessage[]> {
  const response = await requestJson<ChatMessage[]>(`/api/chat/sessions/${sessionId}/messages`)
  return response.data ?? []
}

export async function queryChat(sessionId: string, query: string): Promise<ChatQueryData> {
  const response = await requestJson<ChatQueryData>("/api/chat/query", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      query,
    }),
  })

  if (!response.data) {
    throw new Error("服务未返回问答结果。")
  }

  return response.data
}

function parseSseBlock(block: string): ChatStreamEvent | null {
  const lines = block
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length === 0) {
    return null
  }

  const eventLine = lines.find((line) => line.startsWith("event:"))
  const dataLine = lines.find((line) => line.startsWith("data:"))

  if (!eventLine || !dataLine) {
    return null
  }

  const event = eventLine.slice("event:".length).trim()
  const dataText = dataLine.slice("data:".length).trim()
  const data = JSON.parse(dataText) as ChatStreamEvent["data"]

  return {
    event,
    data,
  } as ChatStreamEvent
}

async function throwStreamError(response: Response): Promise<never> {
  try {
    const payload = (await response.json()) as {
      success?: boolean
      message?: string
      error?: { code?: string; detail?: string } | null
    }

    throw new ApiRequestError(
      payload.error?.detail ?? payload.message ?? "流式请求失败。",
      {
        code: payload.error?.code ?? "STREAM_REQUEST_FAILED",
        status: response.status,
      },
    )
  } catch (error) {
    if (error instanceof ApiRequestError) {
      throw error
    }

    throw new ApiRequestError("流式请求失败。", {
      code: "STREAM_REQUEST_FAILED",
      status: response.status,
    })
  }
}

export async function* streamChat(
  sessionId: string,
  query: string,
): AsyncGenerator<ChatStreamEvent, void, void> {
  const response = await fetch(buildApiUrl("/api/chat/stream"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      session_id: sessionId,
      query,
    }),
  })

  if (!response.ok) {
    await throwStreamError(response)
  }

  if (!response.body) {
    throw new ApiRequestError("服务未返回可读取的流。", {
      code: "STREAM_NOT_AVAILABLE",
      status: response.status,
    })
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done })

    let separatorIndex = buffer.indexOf("\n\n")

    while (separatorIndex >= 0) {
      const block = buffer.slice(0, separatorIndex)
      buffer = buffer.slice(separatorIndex + 2)
      const event = parseSseBlock(block)

      if (event) {
        yield event
      }

      separatorIndex = buffer.indexOf("\n\n")
    }

    if (done) {
      const finalEvent = parseSseBlock(buffer)
      if (finalEvent) {
        yield finalEvent
      }
      break
    }
  }
}
