<script setup lang="ts">
import { onMounted, ref } from "vue"

import ChatWorkspacePanel from "@/components/chat/ChatWorkspacePanel.vue"
import SessionSidebar from "@/components/chat/SessionSidebar.vue"
import DocumentManagerPanel from "@/components/documents/DocumentManagerPanel.vue"
import TaskStatusPanel from "@/components/documents/TaskStatusPanel.vue"
import { useSystemStore } from "@/stores/system"

const systemStore = useSystemStore()
const leftSidebarCollapsed = ref(false)
const rightSidebarTab = ref<'documents' | 'tasks'>('documents')

onMounted(() => {
  void systemStore.loadHealth()
})

function toggleLeftSidebar() {
  leftSidebarCollapsed.value = !leftSidebarCollapsed.value
}
</script>

<template>
  <el-config-provider>
    <div class="app-shell">
      <div class="workspace-frame">
        <!-- 左侧会话栏 - 可折叠 -->
        <aside v-if="!leftSidebarCollapsed" class="nav-rail panel">
          <div class="rail-intro">
            <h1>RAG 助手</h1>
            <p class="rail-copy">智能文档检索</p>
          </div>
          <SessionSidebar />
          <button class="collapse-btn" @click="toggleLeftSidebar" title="收起侧边栏">
            <span>‹</span>
          </button>
        </aside>

        <!-- 展开按钮 -->
        <button v-else class="expand-btn" @click="toggleLeftSidebar" title="展开侧边栏">
          <span>›</span>
        </button>

        <!-- 中间主工作区 -->
        <main class="main-stage panel">
          <header class="stage-header">
            <h2>研究工作区</h2>
            <div v-if="systemStore.healthStatus" class="status-indicator" :class="systemStore.healthStatus">
              <span class="status-dot"></span>
              <span class="status-text">{{ systemStore.healthStatus === 'ok' ? '正常' : '异常' }}</span>
            </div>
          </header>

          <el-alert
            v-if="systemStore.errorMessage"
            class="stage-alert"
            :closable="false"
            :description="systemStore.errorMessage"
            show-icon
            title="后端连接失败"
            type="error"
          />

          <div class="stage-body">
            <ChatWorkspacePanel />
          </div>
        </main>

        <!-- 右侧上下文栏 - 标签页 -->
        <aside class="context-rail panel">
          <div class="rail-tabs">
            <button
              class="tab-btn"
              :class="{ active: rightSidebarTab === 'documents' }"
              @click="rightSidebarTab = 'documents'"
            >
              文档
            </button>
            <button
              class="tab-btn"
              :class="{ active: rightSidebarTab === 'tasks' }"
              @click="rightSidebarTab = 'tasks'"
            >
              任务
            </button>
          </div>

          <div class="tab-content">
            <DocumentManagerPanel v-show="rightSidebarTab === 'documents'" />
            <TaskStatusPanel v-show="rightSidebarTab === 'tasks'" />
          </div>
        </aside>
      </div>
    </div>
  </el-config-provider>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&display=swap');

:global(:root) {
  --color-earth-50: #faf8f5;
  --color-earth-100: #f5f0e8;
  --color-earth-200: #ebe3d5;
  --color-earth-300: #dccfba;
  --color-earth-400: #c9b89a;
  --color-earth-500: #b39f7f;
  --color-earth-600: #9a8567;
  --color-earth-700: #7d6b52;
  --color-earth-800: #5f5240;
  --color-earth-900: #4a4032;

  --color-terracotta-500: #d16645;
  --color-moss-500: #74955b;
  --color-amber-500: #f5a52a;

  --color-cream: #fffef9;
  --color-sand: #f9f6f0;

  --shadow-sm: 0 2px 8px rgba(90, 70, 50, 0.04);
  --shadow-md: 0 4px 16px rgba(90, 70, 50, 0.08);

  --radius-sm: 12px;
  --radius-md: 16px;
  --radius-lg: 20px;
}

:global(body) {
  margin: 0;
  font-family: "LXGW WenKai", "Source Han Serif SC", "Noto Serif SC", Georgia, serif;
  background: var(--color-sand);
  color: var(--color-earth-900);
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}

.app-shell {
  min-height: 100vh;
  padding: 32px;
}

h1, h2 {
  margin: 0;
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  line-height: 1.3;
  color: var(--color-earth-900);
}

h1 {
  font-size: 22px;
}

h2 {
  font-size: 18px;
}

/* 布局 - 简化为可折叠的三栏 */
.workspace-frame {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) 320px;
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 64px);
}

.workspace-frame.left-collapsed {
  grid-template-columns: auto minmax(0, 1fr) 320px;
}

/* 面板基础样式 - 极简 */
.panel {
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(201, 184, 154, 0.2);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.panel:hover {
  box-shadow: var(--shadow-md);
}

/* 左侧会话栏 */
.nav-rail {
  width: 240px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 16px;
  position: relative;
}

.rail-intro {
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(201, 184, 154, 0.15);
}

.rail-copy {
  margin: 8px 0 0;
  color: var(--color-earth-600);
  font-size: 13px;
  line-height: 1.5;
}

.collapse-btn {
  position: absolute;
  right: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 48px;
  border: 1px solid rgba(201, 184, 154, 0.2);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-earth-600);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  transition: all 0.2s ease;
  z-index: 10;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 1);
  color: var(--color-earth-900);
  width: 28px;
}

.expand-btn {
  width: 32px;
  height: 64px;
  border: 1px solid rgba(201, 184, 154, 0.2);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-earth-600);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.2s ease;
  align-self: center;
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 1);
  color: var(--color-earth-900);
  transform: scale(1.05);
}

/* 中间主工作区 */
.main-stage {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 32px;
  min-height: 0;
}

.stage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(201, 184, 154, 0.15);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  background: rgba(249, 246, 240, 0.6);
  font-size: 13px;
  color: var(--color-earth-700);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-earth-400);
}

.status-indicator.ok .status-dot {
  background: var(--color-moss-500);
}

.stage-body {
  flex: 1;
  min-height: 0;
}

.stage-alert {
  border-radius: var(--radius-sm);
}

/* 右侧上下文栏 - 标签页 */
.context-rail {
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.rail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid rgba(201, 184, 154, 0.2);
  background: rgba(249, 246, 240, 0.4);
}

.tab-btn {
  flex: 1;
  padding: 14px 16px;
  border: none;
  background: transparent;
  color: var(--color-earth-600);
  font-size: 14px;
  font-weight: 500;
  font-family: "LXGW WenKai", serif;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.5);
  color: var(--color-earth-900);
}

.tab-btn.active {
  color: var(--color-earth-900);
  background: rgba(255, 255, 255, 0.8);
}

.tab-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-terracotta-500);
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .workspace-frame {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .nav-rail {
    width: 100%;
  }

  .collapse-btn,
  .expand-btn {
    display: none;
  }

  .context-rail {
    max-height: 400px;
  }
}

@media (prefers-reduced-motion: reduce) {
  * {
    animation: none !important;
    transition: none !important;
  }
}
</style>
