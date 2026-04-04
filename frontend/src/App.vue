<script setup lang="ts">
import { onMounted } from "vue"

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

      <main class="workspace-grid">
        <section class="panel sessions-panel">
          <div class="panel-header">
            <h2>会话列表</h2>
            <span>为后续多轮问答预留</span>
          </div>
          <el-empty description="第 5 步仅搭建前端骨架，会话能力将在后续步骤接入。" />
        </section>

        <section class="panel chat-panel">
          <div class="panel-header">
            <h2>聊天工作台</h2>
            <span>当前只验证布局和健康检查联通</span>
          </div>

          <el-alert
            v-if="systemStore.errorMessage"
            :closable="false"
            :description="systemStore.errorMessage"
            show-icon
            title="后端连接失败"
            type="error"
          />

          <el-alert
            v-else-if="systemStore.isLoading"
            :closable="false"
            description="正在请求 /api/health 验证前后端联通情况。"
            show-icon
            title="正在检查后端健康状态"
            type="info"
          />

          <el-alert
            v-else-if="systemStore.healthStatus"
            :closable="false"
            :description="`服务状态：${systemStore.healthStatus}，环境：${systemStore.appEnv ?? 'unknown'}`"
            show-icon
            title="后端连接成功"
            type="success"
          />

          <div class="chat-placeholder">
            <el-card shadow="never">
              <template #header>聊天输入区占位</template>
              <p>后续步骤将在这里接入会话、消息列表、同步问答和 SSE 流式输出。</p>
            </el-card>

            <el-card shadow="never">
              <template #header>引用展示区占位</template>
              <p>当前阶段先保留布局位置，后续检索和引用字段完成后再接入真实数据。</p>
            </el-card>
          </div>
        </section>

        <section class="panel right-column">
          <div class="stack">
            <section class="sub-panel">
              <div class="panel-header">
                <h2>文档管理</h2>
                <span>上传与文档列表将在后续步骤实现</span>
              </div>
              <el-empty description="文档上传、列表和详情接口尚未接入。" />
            </section>

            <section class="sub-panel">
              <div class="panel-header">
                <h2>任务状态</h2>
                <span>异步任务链路将在后续步骤实现</span>
              </div>
              <ul class="status-list">
                <li>UPLOADED</li>
                <li>PARSING</li>
                <li>CHUNKING</li>
                <li>EMBEDDING</li>
                <li>READY</li>
                <li>FAILED</li>
              </ul>
            </section>
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
  margin-bottom: 24px;
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
  grid-template-columns: 280px minmax(0, 1fr) 320px;
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

.chat-placeholder {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.stack {
  display: grid;
  gap: 20px;
}

.sub-panel {
  padding: 20px;
}

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
  color: #334155;
  font-weight: 600;
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
