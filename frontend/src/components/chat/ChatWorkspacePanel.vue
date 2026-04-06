<script setup lang="ts">
import { computed, ref } from "vue"

import { useChatStore } from "@/stores/chat"

const chatStore = useChatStore()
const draft = ref("")

const canSend = computed(() => draft.value.trim().length > 0 && !chatStore.isSending)

function getToolCallStatusLabel(status: string): string {
  if (status === "pending") {
    return "调用中"
  }

  if (status === "success") {
    return "调用成功"
  }

  return "调用失败"
}

function getToolCallSummary(toolCall: {
  result_summary: string | null
  error_detail: string | null
  status: string
}): string {
  if (toolCall.status === "pending") {
    return "工具调用中..."
  }

  return toolCall.result_summary ?? toolCall.error_detail ?? "工具调用已完成。"
}

function isVisualCitation(citation: {
  source_type: string
}): boolean {
  return citation.source_type === "image"
}

function isGraphCitation(citation: {
  source_type: string
}): boolean {
  return citation.source_type === "graph"
}

function getCitationLabel(citation: {
  source_type: string
  asset_label: string | null
}): string {
  if (citation.source_type === "text") {
    return "文本引用"
  }

  if (citation.source_type === "graph") {
    return "图谱引用"
  }

  return citation.asset_label ?? "视觉引用"
}

async function send() {
  if (!canSend.value) {
    return
  }

  const content = draft.value
  draft.value = ""
  await chatStore.sendMessage(content)
}
</script>

<template>
  <section class="panel chat-panel">
    <div class="panel-header">
      <div>
        <h2>聊天工作台</h2>
        <span>
          {{
            chatStore.selectedSession
              ? `当前会话：${chatStore.selectedSession.title}`
              : "暂无会话，发送第一条消息时会自动创建会话"
          }}
        </span>
      </div>
    </div>

    <el-alert
      v-if="chatStore.errorMessage"
      :closable="false"
      type="error"
      show-icon
      title="聊天请求失败"
      :description="chatStore.errorMessage"
    />

    <div class="message-list">
      <el-empty
        v-if="!chatStore.isLoadingMessages && chatStore.messages.length === 0"
        description="发送第一条问题后，这里会展示知识库回答和引用。"
      />

      <article
        v-for="message in chatStore.messages"
        v-else
        :key="message.id"
        class="message-card"
        :class="message.role"
      >
        <header class="message-header">
          <strong>{{ message.role === "user" ? "用户" : "助手" }}</strong>
          <span v-if="message.isStreaming">流式生成中...</span>
        </header>
        <p class="message-content">{{ message.content || "..." }}</p>

        <div
          v-if="message.role === 'assistant' && message.toolCalls.length > 0"
          class="tool-call-list"
        >
          <div
            v-for="(toolCall, index) in message.toolCalls"
            :key="`${message.id}-tool-${index}`"
            class="tool-call-card"
          >
            <div class="tool-call-header">
              <strong>{{ toolCall.tool_name }}</strong>
              <span>{{ getToolCallStatusLabel(toolCall.status) }}</span>
            </div>
            <p class="tool-call-summary">
              {{ getToolCallSummary(toolCall) }}
            </p>
          </div>
        </div>

        <div
          v-if="message.role === 'assistant' && message.citations.length > 0"
          class="citation-list"
        >
          <div
            v-for="(citation, citationIndex) in message.citations"
            :key="`${citation.source_type}-${citation.chunk_id}-${citationIndex}`"
            class="citation-card"
            :class="{ visual: isVisualCitation(citation), graph: isGraphCitation(citation) }"
          >
            <strong>{{ citation.document_name }}</strong>
            <span class="citation-type">{{ getCitationLabel(citation) }}</span>
            <span v-if="citation.page_number !== null">第 {{ citation.page_number }} 页</span>
            <span v-if="citation.source_type === 'graph' && citation.entity_path">
              实体路径：{{ citation.entity_path }}
            </span>
            <p>{{ citation.content }}</p>
          </div>
        </div>
      </article>
    </div>

    <div class="composer">
      <el-input
        v-model="draft"
        type="textarea"
        :rows="4"
        resize="none"
        placeholder="请输入你想从知识库中查询的问题。"
        @keydown.ctrl.enter.prevent="send"
      />
      <div class="composer-actions">
        <span>按 Ctrl + Enter 发送</span>
        <el-button
          type="primary"
          :loading="chatStore.isSending"
          :disabled="!canSend"
          @click="send"
        >
          发送问题
        </el-button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.message-list {
  min-height: 320px;
  display: grid;
  gap: 12px;
  margin-bottom: 16px;
}

.message-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: #f8fafc;
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.message-card.user {
  background: #ecfeff;
}

.message-card.assistant {
  background: #f8fafc;
}

.message-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.message-header span {
  color: #64748b;
  font-size: 12px;
}

.message-content {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.7;
}

.citation-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.tool-call-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.tool-call-card {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(236, 253, 245, 0.9);
  border: 1px solid rgba(34, 197, 94, 0.18);
  display: grid;
  gap: 4px;
}

.tool-call-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.tool-call-header span {
  color: #166534;
  font-size: 12px;
}

.tool-call-summary {
  margin: 0;
  color: #334155;
  line-height: 1.6;
}

.citation-card {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 4px;
}

.citation-card.visual {
  background: rgba(255, 247, 237, 0.92);
  border-color: rgba(249, 115, 22, 0.2);
}

.citation-card.graph {
  background: rgba(239, 246, 255, 0.95);
  border-color: rgba(59, 130, 246, 0.22);
}

.citation-card span,
.composer-actions span {
  color: #64748b;
  font-size: 12px;
}

.citation-type {
  color: #9a3412;
  font-weight: 600;
}

.citation-card.graph .citation-type {
  color: #1d4ed8;
}

.citation-card p {
  margin: 0;
  color: #334155;
  line-height: 1.6;
}

.composer {
  display: grid;
  gap: 10px;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}
</style>
