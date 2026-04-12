<script setup lang="ts">
import { computed } from "vue"

import { useDocumentStore } from "@/stores/documents"

const documentStore = useDocumentStore()

const statusRows = computed(() => [
  { label: "已跟踪文档", value: String(documentStore.trackedCount) },
  { label: "处理中任务", value: String(documentStore.activeTaskCount) },
  { label: "最近状态", value: documentStore.selectedItem?.taskStatus ?? "未选择" },
  { label: "最近文档", value: documentStore.selectedItem?.name ?? "暂无" },
])
</script>

<template>
  <section class="sub-panel support-module-panel">
    <div class="panel-header">
      <div class="panel-copy">
        <p class="support-eyebrow">支持模块</p>
        <h2>任务摘要</h2>
        <span>保留关键处理进展，帮助你确认当前资料是否已准备好进入问答流。</span>
      </div>
    </div>

    <div class="support-block">
      <ul class="status-list">
        <li
          v-for="row in statusRows"
          :key="row.label"
          :data-testid="`task-summary-${row.label}`"
        >
          <span>{{ row.label }}</span>
          <strong :data-testid="`task-summary-value-${row.label}`">{{ row.value }}</strong>
        </li>
      </ul>

      <p class="status-hint">
        任务状态会在页面打开期间自动轮询；刷新后会从本地保存的文档清单恢复。
      </p>
    </div>
  </section>
</template>

<style scoped>
.support-module-panel {
  display: grid;
  gap: 12px;
}

.panel-copy {
  display: grid;
  gap: 4px;
}

.panel-copy h2 {
  margin: 0;
}

.support-eyebrow {
  margin: 0;
  color: #0f766e;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.support-block {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.9);
  padding: 14px;
}

.status-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.status-list li {
  padding: 10px 12px;
  border-radius: 12px;
  background: #ffffff;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #334155;
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.status-list span,
.status-hint {
  color: #64748b;
  font-size: 12px;
}

.status-hint {
  margin: 12px 0 0;
  line-height: 1.6;
}
</style>
