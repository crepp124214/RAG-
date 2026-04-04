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
  <section class="sub-panel">
    <div class="panel-header">
      <div>
        <h2>任务状态</h2>
        <span>基于当前已跟踪文档展示异步处理进展</span>
      </div>
    </div>

    <ul class="status-list">
      <li
        v-for="row in statusRows"
        :key="row.label"
      >
        <span>{{ row.label }}</span>
        <strong>{{ row.value }}</strong>
      </li>
    </ul>

    <p class="status-hint">
      任务状态会在页面打开期间自动轮询；刷新后会从本地保存的文档清单恢复。
    </p>
  </section>
</template>

<style scoped>
.status-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 10px;
}

.status-list li {
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #334155;
}

.status-list span,
.status-hint {
  color: #64748b;
  font-size: 13px;
}

.status-hint {
  margin: 14px 0 0;
}
</style>
