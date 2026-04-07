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
  <section class="panel chat-panel workspace-stage">
    <header class="panel-header session-stage-header">
      <div class="session-stage-copy">
        <span class="session-stage-eyebrow">当前知识会话</span>
        <h2>
          {{
            chatStore.selectedSession
              ? chatStore.selectedSession.title
              : "从这里开始你的第一条知识对话"
          }}
        </h2>
        <p>
          {{
            chatStore.selectedSession
              ? "围绕当前会话持续整理问题、答案、引用和工具结果。"
              : "暂无会话，发送第一条消息时会自动创建会话。"
          }}
        </p>
      </div>
      <div
        v-if="chatStore.selectedSession"
        class="session-stage-meta"
      >
        <span>知识工作区</span>
      </div>
    </header>

    <el-alert
      v-if="chatStore.errorMessage"
      :closable="false"
      type="error"
      show-icon
      title="聊天请求失败"
      :description="chatStore.errorMessage"
    />

    <div class="message-list conversation-stream">
      <el-empty
        v-if="!chatStore.isLoadingMessages && chatStore.messages.length === 0"
        description="发送第一条问题后，这里会展示知识库回答和引用。"
      />

      <article
        v-for="message in chatStore.messages"
        v-else
        :key="message.id"
        class="message-card workspace-turn"
        :class="message.role"
      >
        <header class="message-header">
          <div class="message-speaker">
            <strong>{{ message.role === "user" ? "你" : "知识助手" }}</strong>
            <span>{{ message.role === "user" ? "提问与指令" : "回答与依据" }}</span>
          </div>
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

    <div class="composer workspace-composer">
      <div class="composer-heading">
        <strong>继续当前工作区</strong>
        <span>在这里继续整理问题、结论或下一步动作</span>
      </div>
      <el-input
        v-model="draft"
        type="textarea"
        :rows="4"
        resize="none"
        placeholder="继续输入你的问题、总结或需要助手展开的方向。"
        @keydown.ctrl.enter.prevent="send"
      />
      <div class="composer-actions">
        <span>Ctrl + Enter 发送</span>
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
.workspace-stage {
  display: grid;
  gap: 18px;
  padding: 24px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.96) 100%);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.06);
}

.session-stage-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding-bottom: 18px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
}

.session-stage-copy {
  display: grid;
  gap: 8px;
}

.session-stage-eyebrow {
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.session-stage-copy h2 {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
  color: #0f172a;
}

.session-stage-copy p {
  margin: 0;
  max-width: 720px;
  color: #475569;
  line-height: 1.7;
}

.session-stage-meta {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.04);
  color: #475569;
  font-size: 12px;
  font-weight: 600;
}

.message-list {
  min-height: 420px;
  display: grid;
  gap: 0;
}

.conversation-stream {
  padding: 0 8px 0 0;
}

.message-card {
  padding: 20px 8px 22px;
  border-radius: 0;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.workspace-turn:last-child {
  border-bottom: none;
}

.message-card.user {
  background: transparent;
}

.message-card.assistant {
  background: transparent;
}

.message-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
  align-items: flex-start;
}

.message-speaker {
  display: grid;
  gap: 4px;
}

.message-speaker strong {
  color: #0f172a;
  font-size: 15px;
}

.message-speaker span {
  color: #64748b;
  font-size: 12px;
}

.message-header span {
  color: #64748b;
  font-size: 12px;
}

.message-content {
  margin: 0;
  white-space: pre-wrap;
  color: #1e293b;
  line-height: 1.9;
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
  gap: 12px;
}

.workspace-composer {
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
}

.composer-heading {
  display: grid;
  gap: 4px;
}

.composer-heading strong {
  color: #0f172a;
  font-size: 15px;
}

.composer-heading span {
  color: #64748b;
  font-size: 13px;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

:deep(.workspace-composer .el-textarea__inner) {
  min-height: 132px !important;
  padding: 16px 18px;
  border-radius: 18px;
  border-color: rgba(148, 163, 184, 0.2);
  box-shadow: none;
  background: rgba(248, 250, 252, 0.8);
  color: #0f172a;
  line-height: 1.8;
}

:deep(.workspace-composer .el-textarea__inner:focus) {
  border-color: rgba(15, 118, 110, 0.42);
  background: #ffffff;
}
</style>
