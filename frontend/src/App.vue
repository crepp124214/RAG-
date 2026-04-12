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
      <div class="workspace-frame">
        <aside class="nav-rail panel">
          <div class="rail-intro">
            <p class="eyebrow">Knowledge Workspace</p>
            <h1>RAG 智能文档检索助手</h1>
            <p class="rail-copy">面向研究与证据整理的桌面化工作区。</p>
          </div>
          <SessionSidebar />
        </aside>

        <main class="main-stage panel">
          <header class="stage-header">
            <div>
              <p class="eyebrow">Professional Research Flow</p>
              <h2>研究工作区</h2>
            </div>
            <section class="shell-status">
              <span class="status-label">系统状态</span>
              <strong v-if="systemStore.errorMessage">连接受阻</strong>
              <strong v-else-if="systemStore.isLoading">检查中</strong>
              <strong v-else>{{ systemStore.healthSummary ?? "未知" }}</strong>
              <p v-if="!systemStore.errorMessage && !systemStore.isLoading">
                服务状态：{{ systemStore.healthStatus ?? "unknown" }}，环境：{{ systemStore.appEnv ?? "unknown" }}
              </p>
            </section>
          </header>

          <el-alert
            v-if="systemStore.errorMessage"
            class="stage-alert"
            :closable="false"
            :description="`${systemStore.errorMessage} 请先恢复后端服务后再继续当前研究流程。`"
            show-icon
            title="后端连接失败"
            type="error"
          />

          <el-alert
            v-else-if="systemStore.isLoading"
            class="stage-alert"
            :closable="false"
            description="正在请求 /api/health 验证前后端联通情况。"
            show-icon
            title="正在检查后端健康状态"
            type="info"
          />

          <div class="stage-body">
            <ChatWorkspacePanel />
          </div>
        </main>

        <aside class="evidence-rail panel">
          <div class="rail-header">
            <p class="eyebrow">Context Layer</p>
            <h2>证据与任务</h2>
          </div>
          <div class="stack">
            <DocumentManagerPanel />
            <TaskStatusPanel />
          </div>
        </aside>
      </div>
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
  padding: 20px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #64748b;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h1,
h2 {
  margin: 0;
}

.workspace-frame {
  display: grid;
  grid-template-columns: 240px minmax(0, 1.6fr) 320px;
  gap: 16px;
  min-height: calc(100vh - 40px);
  padding: 16px;
  border-radius: 28px;
  background: rgba(248, 250, 252, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.12);
}

.panel {
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(20px);
}

.nav-rail,
.main-stage,
.evidence-rail {
  min-height: 0;
}

.nav-rail {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
}

.rail-intro,
.rail-header {
  padding-bottom: 4px;
}

.rail-copy {
  margin: 10px 0 0;
  color: #475569;
  font-size: 13px;
  line-height: 1.5;
}

.main-stage {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr);
  gap: 18px;
  padding: 22px;
}

.stage-header {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  align-items: flex-start;
}

.stage-body {
  min-height: 0;
}

.stage-alert {
  margin: -2px 0 0;
}

.shell-status {
  min-width: 220px;
  max-width: 280px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(241, 245, 249, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.shell-status strong {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
  color: #0f172a;
}

.shell-status p,
.status-label {
  margin: 0;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.status-label {
  display: block;
  margin-bottom: 6px;
}

.evidence-rail {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
  background: rgba(255, 255, 255, 0.58);
}

.stack {
  display: grid;
  gap: 16px;
}

@media (max-width: 1100px) {
  .workspace-frame {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .stage-header {
    flex-direction: column;
  }

  .shell-status {
    width: 100%;
    max-width: none;
  }
}
</style>
