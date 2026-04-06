import { defineStore } from "pinia"

import {
  createSession,
  fetchMessages,
  fetchSessions,
  streamChat,
  type ChatMessage,
  type ChatSession,
  type Citation,
  type ToolCall,
} from "@/services/chat"

const STORAGE_KEY = "rag-selected-session-id"

export interface ChatMessageItem {
  id: string
  sessionId: string
  role: "user" | "assistant"
  content: string
  createdAt: string
  updatedAt: string
  citations: Citation[]
  toolCalls: ToolCall[]
  isStreaming?: boolean
  isTemporary?: boolean
}

interface ChatState {
  sessions: ChatSession[]
  selectedSessionId: string | null
  messages: ChatMessageItem[]
  isLoadingSessions: boolean
  isLoadingMessages: boolean
  isSending: boolean
  errorMessage: string | null
}

function readSelectedSessionId(): string | null {
  if (typeof localStorage === "undefined") {
    return null
  }

  return localStorage.getItem(STORAGE_KEY)
}

function writeSelectedSessionId(sessionId: string | null): void {
  if (typeof localStorage === "undefined") {
    return
  }

  if (!sessionId) {
    localStorage.removeItem(STORAGE_KEY)
    return
  }

  localStorage.setItem(STORAGE_KEY, sessionId)
}

function normalizeMessage(message: ChatMessage): ChatMessageItem {
  return {
    id: message.id,
    sessionId: message.session_id,
    role: message.role as "user" | "assistant",
    content: message.content,
    createdAt: message.created_at,
    updatedAt: message.updated_at,
    citations: message.citations ?? [],
    toolCalls: message.tool_calls ?? [],
  }
}

function createTemporaryMessage(
  sessionId: string,
  role: "user" | "assistant",
  content: string,
): ChatMessageItem {
  const stamp = new Date().toISOString()
  return {
    id: `temp-${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    sessionId,
    role,
    content,
    createdAt: stamp,
    updatedAt: stamp,
    citations: [],
    toolCalls: [],
    isTemporary: true,
    isStreaming: role === "assistant",
  }
}

function createPendingToolCall(toolName: string, arguments_: Record<string, unknown>): ToolCall {
  return {
    tool_name: toolName,
    arguments: arguments_,
    status: "pending",
    result_summary: null,
    error_code: null,
    error_detail: null,
  }
}

function findToolCallIndex(
  toolCalls: ToolCall[],
  toolName: string,
  arguments_: Record<string, unknown>,
): number {
  const serializedArguments = JSON.stringify(arguments_)
  return toolCalls.findIndex(
    (toolCall) =>
      toolCall.tool_name === toolName &&
      JSON.stringify(toolCall.arguments) === serializedArguments &&
      toolCall.status === "pending",
  )
}

export const useChatStore = defineStore("chat", {
  state: (): ChatState => ({
    sessions: [],
    selectedSessionId: null,
    messages: [],
    isLoadingSessions: false,
    isLoadingMessages: false,
    isSending: false,
    errorMessage: null,
  }),
  getters: {
    selectedSession(state): ChatSession | null {
      return state.sessions.find((session) => session.id === state.selectedSessionId) ?? null
    },
  },
  actions: {
    setSelectedSession(sessionId: string | null) {
      this.selectedSessionId = sessionId
      writeSelectedSessionId(sessionId)
    },

    async hydrate() {
      await this.loadSessions()

      const rememberedSessionId = readSelectedSessionId()
      const preferredSession = this.sessions.find((session) => session.id === rememberedSessionId)

      if (preferredSession) {
        await this.selectSession(preferredSession.id)
        return
      }

      if (this.sessions[0]) {
        await this.selectSession(this.sessions[0].id)
      }
    },

    async loadSessions() {
      this.isLoadingSessions = true
      this.errorMessage = null

      try {
        this.sessions = await fetchSessions()
      } catch (error) {
        this.errorMessage = error instanceof Error ? error.message : "加载会话列表失败。"
      } finally {
        this.isLoadingSessions = false
      }
    },

    async createAndSelectSession() {
      this.errorMessage = null
      const created = await createSession()
      await this.loadSessions()
      await this.selectSession(created.session_id)
    },

    async selectSession(sessionId: string) {
      this.isLoadingMessages = true
      this.errorMessage = null

      try {
        const messages = await fetchMessages(sessionId)
        this.messages = messages.map(normalizeMessage)
        this.setSelectedSession(sessionId)
      } catch (error) {
        this.errorMessage = error instanceof Error ? error.message : "加载消息列表失败。"
      } finally {
        this.isLoadingMessages = false
      }
    },

    async ensureSession(): Promise<string> {
      if (this.selectedSessionId) {
        return this.selectedSessionId
      }

      const created = await createSession()
      await this.loadSessions()
      this.setSelectedSession(created.session_id)
      this.messages = []
      return created.session_id
    },

    async sendMessage(query: string) {
      const trimmedQuery = query.trim()
      if (!trimmedQuery || this.isSending) {
        return
      }

      const sessionId = await this.ensureSession()
      this.errorMessage = null
      this.isSending = true

      const temporaryUserMessage = createTemporaryMessage(sessionId, "user", trimmedQuery)
      const temporaryAssistantMessage = createTemporaryMessage(sessionId, "assistant", "")

      this.messages.push(temporaryUserMessage, temporaryAssistantMessage)

      try {
        for await (const event of streamChat(sessionId, trimmedQuery)) {
          if (event.event === "token") {
            temporaryAssistantMessage.content += event.data.content
            continue
          }

          if (event.event === "tool_call") {
            temporaryAssistantMessage.toolCalls.push(
              createPendingToolCall(event.data.tool_name, event.data.arguments),
            )
            continue
          }

          if (event.event === "tool_result") {
            const toolCallIndex = findToolCallIndex(
              temporaryAssistantMessage.toolCalls,
              event.data.tool_name,
              event.data.arguments,
            )

            if (toolCallIndex >= 0) {
              temporaryAssistantMessage.toolCalls[toolCallIndex] = event.data
            } else {
              temporaryAssistantMessage.toolCalls.push(event.data)
            }
            continue
          }

          if (event.event === "citation") {
            temporaryAssistantMessage.citations.push(event.data)
            continue
          }

          if (event.event === "message_end") {
            temporaryUserMessage.id = event.data.user_message_id
            temporaryUserMessage.isTemporary = false
            temporaryAssistantMessage.id = event.data.assistant_message_id
            temporaryAssistantMessage.content = event.data.answer
            temporaryAssistantMessage.citations = event.data.citations
            temporaryAssistantMessage.toolCalls = event.data.tool_calls
            temporaryAssistantMessage.isTemporary = false
            temporaryAssistantMessage.isStreaming = false
            await this.loadSessions()
            return
          }

          if (event.event === "error") {
            throw new Error(event.data.detail)
          }
        }
      } catch (error) {
        this.messages = this.messages.filter(
          (message) =>
            message.id !== temporaryUserMessage.id && message.id !== temporaryAssistantMessage.id,
        )
        this.errorMessage =
          error instanceof Error ? error.message : "发送消息时发生未知错误。"
      } finally {
        this.isSending = false
      }
    },
  },
})
