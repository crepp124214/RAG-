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
  gap: 22px;
  padding: 0;
  border-radius: 0;
  background: transparent;
  border: none;
  box-shadow: none;
}

.session-stage-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
  padding-bottom: 20px;
  border-bottom: 2px solid;
  border-image: linear-gradient(90deg,
    var(--color-terracotta-300),
    var(--color-amber-300),
    transparent) 1;
}

.session-stage-copy {
  display: grid;
  gap: 10px;
}

.session-stage-eyebrow {
  color: var(--color-terracotta-600);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-family: "Inter", sans-serif;
}

.session-stage-copy h2 {
  margin: 0;
  font-size: 32px;
  line-height: 1.25;
  color: var(--color-earth-900);
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  font-variation-settings: "soft" 70;
}

.session-stage-copy p {
  margin: 0;
  max-width: 680px;
  color: var(--color-earth-700);
  line-height: 1.7;
  font-size: 15px;
}

.session-stage-meta {
  display: inline-flex;
  align-items: center;
  padding: 10px 16px;
  border-radius: 20px 24px 22px 26px / 22px 26px 24px 20px;
  background:
    linear-gradient(135deg,
      rgba(245, 165, 42, 0.12),
      rgba(116, 149, 91, 0.1));
  border: 1.5px solid var(--color-earth-300);
  color: var(--color-earth-700);
  font-size: 13px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(90, 70, 50, 0.06);
}

.message-list {
  min-height: 420px;
  max-height: 600px;
  display: grid;
  gap: 0;
  overflow-y: auto;
  padding-right: 12px;
}

.message-list::-webkit-scrollbar {
  width: 8px;
}

.message-list::-webkit-scrollbar-track {
  background: rgba(201, 184, 154, 0.1);
  border-radius: 10px;
}

.message-list::-webkit-scrollbar-thumb {
  background: var(--color-earth-400);
  border-radius: 10px;
  transition: background 0.3s ease;
}

.message-list::-webkit-scrollbar-thumb:hover {
  background: var(--color-earth-500);
}

.conversation-stream {
  padding: 0;
}

.message-card {
  padding: 24px 16px 26px;
  border-radius: 0;
  background: transparent;
  border: none;
  border-bottom: 1px solid rgba(201, 184, 154, 0.2);
  transition: background 0.3s ease;
  animation: messageSlideIn 0.5s ease-out backwards;
}

@keyframes messageSlideIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.workspace-turn:last-child {
  border-bottom: none;
}

.message-card:hover {
  background:
    linear-gradient(90deg,
      rgba(255, 254, 249, 0.6),
      transparent);
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
  gap: 14px;
  margin-bottom: 12px;
  align-items: flex-start;
}

.message-speaker {
  display: grid;
  gap: 5px;
}

.message-speaker strong {
  color: var(--color-earth-900);
  font-size: 16px;
  font-weight: 600;
  font-family: "Fraunces", "LXGW WenKai", serif;
}

.message-speaker span {
  color: var(--color-earth-600);
  font-size: 12px;
  opacity: 0.85;
}

.message-header > span {
  color: var(--color-earth-600);
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(245, 165, 42, 0.1);
  font-weight: 500;
}

.message-content {
  margin: 0;
  white-space: pre-wrap;
  color: var(--color-earth-800);
  line-height: 1.85;
  font-size: 15px;
}

.citation-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.tool-call-list {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.tool-call-card {
  padding: 14px 16px;
  border-radius: 16px 20px 18px 22px / 18px 22px 20px 16px;
  background:
    linear-gradient(135deg,
      rgba(246, 248, 244, 0.95),
      rgba(233, 240, 227, 0.9));
  border: 1.5px solid var(--color-moss-300);
  display: grid;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(90, 119, 69, 0.08);
  transition: all 0.3s ease;
}

.tool-call-card:hover {
  border-color: var(--color-moss-400);
  box-shadow: 0 4px 12px rgba(90, 119, 69, 0.12);
  transform: translateY(-1px);
}

.tool-call-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.tool-call-header strong {
  font-family: "Fraunces", serif;
  font-weight: 600;
  color: var(--color-moss-800);
}

.tool-call-header span {
  color: var(--color-moss-700);
  font-size: 12px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 8px;
  background: rgba(116, 149, 91, 0.15);
}

.tool-call-summary {
  margin: 0;
  color: var(--color-earth-700);
  line-height: 1.65;
  font-size: 14px;
}

.citation-card {
  padding: 14px 16px;
  border-radius: 16px 20px 18px 22px / 18px 22px 20px 16px;
  background:
    linear-gradient(135deg,
      rgba(255, 254, 249, 0.95),
      rgba(249, 246, 240, 0.9));
  border: 1.5px solid var(--color-earth-300);
  display: grid;
  gap: 6px;
  box-shadow: 0 2px 8px rgba(90, 70, 50, 0.06);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.citation-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: linear-gradient(180deg,
    var(--color-earth-500),
    var(--color-earth-400));
  opacity: 0.6;
}

.citation-card:hover {
  border-color: var(--color-earth-400);
  box-shadow: 0 4px 16px rgba(90, 70, 50, 0.1);
  transform: translateY(-1px);
}

.citation-card.visual {
  background:
    linear-gradient(135deg,
      rgba(253, 246, 243, 0.95),
      rgba(250, 232, 223, 0.9));
  border-color: var(--color-terracotta-300);
}

.citation-card.visual::before {
  background: linear-gradient(180deg,
    var(--color-terracotta-500),
    var(--color-terracotta-400));
}

.citation-card.graph {
  background:
    linear-gradient(135deg,
      rgba(246, 248, 244, 0.95),
      rgba(233, 240, 227, 0.9));
  border-color: var(--color-moss-300);
}

.citation-card.graph::before {
  background: linear-gradient(180deg,
    var(--color-moss-600),
    var(--color-moss-500));
}

.citation-card strong {
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  color: var(--color-earth-900);
  font-size: 15px;
}

.citation-card span {
  color: var(--color-earth-600);
  font-size: 12px;
  opacity: 0.9;
}

.citation-type {
  color: var(--color-earth-700);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 8px;
  background: rgba(179, 159, 127, 0.15);
  display: inline-block;
  width: fit-content;
}

.citation-card.visual .citation-type {
  color: var(--color-terracotta-700);
  background: rgba(209, 102, 69, 0.15);
}

.citation-card.graph .citation-type {
  color: var(--color-moss-700);
  background: rgba(116, 149, 91, 0.15);
}

.citation-card p {
  margin: 0;
  color: var(--color-earth-700);
  line-height: 1.7;
  font-size: 14px;
}

.composer {
  display: grid;
  gap: 14px;
}

.workspace-composer {
  padding: 22px 24px;
  border-radius: var(--radius-organic-md);
  background:
    linear-gradient(135deg,
      rgba(255, 254, 249, 0.95),
      rgba(249, 246, 240, 0.9));
  border: 2px solid var(--color-earth-300);
  box-shadow:
    var(--shadow-soft),
    inset 0 1px 0 rgba(255, 255, 255, 0.7);
  transition: all 0.3s ease;
}

.workspace-composer:focus-within {
  border-color: var(--color-terracotta-400);
  box-shadow:
    var(--shadow-medium),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.composer-heading {
  display: grid;
  gap: 5px;
}

.composer-heading strong {
  color: var(--color-earth-900);
  font-size: 16px;
  font-weight: 600;
  font-family: "Fraunces", "LXGW WenKai", serif;
}

.composer-heading span {
  color: var(--color-earth-600);
  font-size: 13px;
  opacity: 0.9;
}

.composer-actions {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
}

.composer-actions span {
  color: var(--color-earth-600);
  font-size: 12px;
  font-family: "Inter", monospace;
  padding: 4px 10px;
  border-radius: 8px;
  background: rgba(179, 159, 127, 0.1);
}

:deep(.workspace-composer .el-textarea__inner) {
  min-height: 140px !important;
  padding: 18px 20px;
  border-radius: var(--radius-organic-sm);
  border: 1.5px solid var(--color-earth-300);
  box-shadow: inset 0 1px 3px rgba(90, 70, 50, 0.06);
  background:
    linear-gradient(135deg,
      rgba(255, 255, 255, 0.9),
      rgba(249, 246, 240, 0.85));
  color: var(--color-earth-900);
  line-height: 1.8;
  font-size: 15px;
  font-family: "LXGW WenKai", serif;
  transition: all 0.3s ease;
}

:deep(.workspace-composer .el-textarea__inner:focus) {
  border-color: var(--color-terracotta-400);
  background: rgba(255, 255, 255, 0.98);
  box-shadow:
    inset 0 1px 3px rgba(90, 70, 50, 0.08),
    0 0 0 3px rgba(209, 102, 69, 0.1);
}

:deep(.workspace-composer .el-textarea__inner::placeholder) {
  color: var(--color-earth-500);
  opacity: 0.7;
}
</style>
