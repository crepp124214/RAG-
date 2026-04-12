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
  <section class="task-panel">
    <div class="panel-header">
      <h3>任务摘要</h3>
    </div>

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
      任务状态会自动轮询更新
    </p>
  </section>
</template>

<style scoped>
.task-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(201, 184, 154, 0.15);
}

.panel-header h3 {
  margin: 0;
  font-size: 15px;
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  color: var(--color-earth-900);
}

.status-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(249, 246, 240, 0.6);
  border: 1px solid rgba(201, 184, 154, 0.15);
}

.status-list li span {
  color: var(--color-earth-600);
  font-size: 13px;
}

.status-list li strong {
  color: var(--color-earth-900);
  font-size: 14px;
  font-weight: 600;
}

.status-hint {
  margin: 0;
  padding-top: 12px;
  border-top: 1px solid rgba(201, 184, 154, 0.15);
  color: var(--color-earth-600);
  font-size: 12px;
  line-height: 1.5;
}
</style>
