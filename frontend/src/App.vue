<script setup lang="ts">
import { onMounted } from "vue"

import ChatWorkspacePanel from "@/components/chat/ChatWorkspacePanel.vue"
import SessionSidebar from "@/components/chat/SessionSidebar.vue"
import DocumentManagerPanel from "@/components/documents/DocumentManagerPanel.vue"
import TaskStatusPanel from "@/components/documents/TaskStatusPanel.vue"
import { useSystemStore } from "@/stores/system"

const systemStore = useSystemStore()

onMounted(() => {
  void systemStore.loadHealth()
})
</script>

<template>
  <el-config-provider>
    <div class="app-shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">第一阶段最小可运行产品</p>
          <h1>RAG 智能文档检索助手</h1>
        </div>
        <div class="status-card">
          <span class="status-label">后端健康状态</span>
          <strong
            v-if="systemStore.healthSummary"
            class="status-value"
          >
            {{ systemStore.healthSummary }}
          </strong>
          <strong
            v-else
            class="status-value"
          >
            未知
          </strong>
        </div>
      </header>

      <el-alert
        v-if="systemStore.errorMessage"
        class="top-alert"
        :closable="false"
        :description="systemStore.errorMessage"
        show-icon
        title="后端连接失败"
        type="error"
      />

      <el-alert
        v-else-if="systemStore.isLoading"
        class="top-alert"
        :closable="false"
        description="正在请求 /api/health 验证前后端联通情况。"
        show-icon
        title="正在检查后端健康状态"
        type="info"
      />

      <el-alert
        v-else-if="systemStore.healthStatus"
        class="top-alert"
        :closable="false"
        :description="`服务状态：${systemStore.healthStatus}，环境：${systemStore.appEnv ?? 'unknown'}`"
        show-icon
        title="后端连接成功"
        type="success"
      />

      <main class="workspace-grid">
        <SessionSidebar />
        <ChatWorkspacePanel />
        <section class="panel right-column">
          <div class="stack">
            <DocumentManagerPanel />
            <TaskStatusPanel />
          </div>
        </section>
      </main>
    </div>
  </el-config-provider>
</template>

<style scoped>
:global(body) {
  margin: 0;
  font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(66, 184, 131, 0.18), transparent 28%),
    linear-gradient(160deg, #f6fbf8 0%, #edf2f7 100%);
  color: #1f2937;
}

:global(*) {
  box-sizing: border-box;
}

.app-shell {
  min-height: 100vh;
  padding: 24px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-bottom: 18px;
}

.top-alert {
  margin-bottom: 18px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #0f766e;
  font-size: 13px;
  letter-spacing: 0.08em;
}

h1,
h2 {
  margin: 0;
}

.status-card {
  min-width: 220px;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.status-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.status-value {
  font-size: 18px;
  color: #0f172a;
}

.workspace-grid {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 360px;
  gap: 20px;
}

.panel,
.sub-panel {
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.panel {
  padding: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: baseline;
  margin-bottom: 18px;
}

.panel-header span {
  color: #64748b;
  font-size: 13px;
}

.stack {
  display: grid;
  gap: 20px;
}

@media (max-width: 1100px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .status-card {
    width: 100%;
  }
}
</style>
