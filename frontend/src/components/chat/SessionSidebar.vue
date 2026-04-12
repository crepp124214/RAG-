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
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-header h2 {
  font-size: 15px;
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  color: var(--color-earth-900);
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.session-card {
  width: 100%;
  border: 1px solid rgba(201, 184, 154, 0.2);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.2s ease;
  position: relative;
}

.session-card:hover {
  border-color: var(--color-earth-400);
  background: rgba(255, 255, 255, 0.9);
  transform: translateX(2px);
}

.session-card.active {
  border-color: var(--color-terracotta-500);
  background: rgba(253, 246, 243, 0.9);
  border-left-width: 3px;
  padding-left: 12px;
}

.session-card strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-earth-900);
  font-family: "LXGW WenKai", serif;
  line-height: 1.4;
}

.session-card span {
  color: var(--color-earth-600);
  font-size: 11px;
  opacity: 0.8;
}
</style>
