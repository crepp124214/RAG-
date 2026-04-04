<script setup lang="ts">
import { onMounted } from "vue"

import { useChatStore } from "@/stores/chat"

const chatStore = useChatStore()

onMounted(() => {
  void chatStore.hydrate()
})
</script>

<template>
  <section class="panel sessions-panel">
    <div class="panel-header">
      <div>
        <h2>会话列表</h2>
        <span>按最近活跃排序，支持自动生成首轮标题</span>
      </div>
      <el-button
        plain
        @click="chatStore.createAndSelectSession()"
      >
        新建会话
      </el-button>
    </div>

    <el-alert
      v-if="chatStore.errorMessage"
      :closable="false"
      type="warning"
      show-icon
      title="会话区域提示"
      :description="chatStore.errorMessage"
    />

    <el-empty
      v-if="!chatStore.isLoadingSessions && chatStore.sessions.length === 0"
      description="还没有会话，点击右上角即可新建。"
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
        <strong>{{ session.title }}</strong>
        <span>{{ session.updated_at }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.session-list {
  display: grid;
  gap: 10px;
}

.session-card {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  background: #f8fafc;
  padding: 12px 14px;
  text-align: left;
  cursor: pointer;
  display: grid;
  gap: 6px;
}

.session-card.active,
.session-card:hover {
  border-color: rgba(15, 118, 110, 0.45);
}

.session-card span {
  color: #64748b;
  font-size: 12px;
}
</style>
