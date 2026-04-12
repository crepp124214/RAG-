<script setup lang="ts">
import { onMounted } from "vue"

import { useChatStore } from "@/stores/chat"

const chatStore = useChatStore()

onMounted(() => {
  void chatStore.hydrate()
})
</script>

<template>
  <section
    class="panel sessions-panel"
    aria-label="会话导航"
  >
    <div class="panel-header">
      <h2>会话</h2>
      <el-button
        plain
        @click="chatStore.createAndSelectSession()"
      >
        新建
      </el-button>
    </div>

    <el-alert
      v-if="chatStore.errorMessage"
      :closable="false"
      type="warning"
      show-icon
      title="会话提示"
      :description="chatStore.errorMessage"
    />

    <el-empty
      v-if="!chatStore.isLoadingSessions && chatStore.sessions.length === 0"
      description="暂无会话"
    />

    <div
      v-else
      class="session-list"
    >
      <button
        v-for="session in chatStore.sessions"
        :key="session.id"
        class="session-card"
        :class="{ active: session.id === chatStore.selectedSessionId }"
        @click="chatStore.selectSession(session.id)"
      >
        <strong :title="session.title">{{ session.title }}</strong>
        <span>{{ session.updated_at }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.sessions-panel {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 12px;
  min-height: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.panel-header h2 {
  font-size: 14px;
}

.session-list {
  display: grid;
  gap: 8px;
  min-height: 0;
  align-content: start;
}

.session-card {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.9);
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  display: grid;
  gap: 4px;
}

.session-card.active,
.session-card:hover {
  border-color: rgba(15, 118, 110, 0.45);
  background: rgba(240, 253, 250, 0.92);
}

.session-card strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.session-card span {
  color: #64748b;
  font-size: 12px;
}
</style>
