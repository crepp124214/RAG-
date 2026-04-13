<script setup lang="ts">
import { onMounted, ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { Delete, Download, Edit, StarFilled } from "@element-plus/icons-vue"

import { useChatStore } from "@/stores/chat"
import SessionSearchBar from "./SessionSearchBar.vue"
import SessionRenameDialog from "./SessionRenameDialog.vue"
import SessionExportDialog from "./SessionExportDialog.vue"

const chatStore = useChatStore()

const renameDialogVisible = ref(false)
const exportDialogVisible = ref(false)
const selectedSessionForAction = ref<string | null>(null)
const selectedSessionTitle = ref("")

onMounted(() => {
  void chatStore.hydrate()
})

function handleSearch(keyword: string) {
  chatStore.setSearchKeyword(keyword)
}

function openRenameDialog(sessionId: string, currentTitle: string) {
  selectedSessionForAction.value = sessionId
  selectedSessionTitle.value = currentTitle
  renameDialogVisible.value = true
}

async function handleRename(sessionId: string, newTitle: string) {
  try {
    await chatStore.renameSession(sessionId, newTitle)
    ElMessage.success("会话重命名成功")
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "重命名失败")
  }
}

async function handleTogglePin(sessionId: string) {
  try {
    await chatStore.togglePinSession(sessionId)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "置顶操作失败")
  }
}

async function handleDelete(sessionId: string, sessionTitle: string) {
  try {
    await ElMessageBox.confirm(`确定要删除会话"${sessionTitle}"吗？此操作不可恢复。`, "删除会话", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    })

    await chatStore.deleteSession(sessionId)
    ElMessage.success("会话已删除")
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error instanceof Error ? error.message : "删除失败")
    }
  }
}

function openExportDialog(sessionId: string, sessionTitle: string) {
  selectedSessionForAction.value = sessionId
  selectedSessionTitle.value = sessionTitle
  exportDialogVisible.value = true
}

async function handleExport(sessionId: string) {
  try {
    const markdown = await chatStore.exportSessionToMarkdown(sessionId)
    const session = chatStore.sessions.find((s) => s.id === sessionId)
    const filename = `${session?.title || "会话"}_${new Date().toISOString().slice(0, 10)}.md`

    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = filename
    link.click()
    URL.revokeObjectURL(url)

    exportDialogVisible.value = false
    ElMessage.success("会话导出成功")
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "导出失败")
  }
}
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

    <SessionSearchBar
      :model-value="chatStore.searchKeyword"
      @search="handleSearch"
    />

    <el-alert
      v-if="chatStore.errorMessage"
      :closable="false"
      type="warning"
      show-icon
      title="会话提示"
      :description="chatStore.errorMessage"
    />

    <el-empty
      v-if="!chatStore.isLoadingSessions && chatStore.sortedSessions.length === 0"
      description="暂无会话"
    />

    <div
      v-else
      class="session-list"
    >
      <div
        v-for="session in chatStore.sortedSessions"
        :key="session.id"
        class="session-card"
        :class="{ active: session.id === chatStore.selectedSessionId, pinned: session.is_pinned }"
      >
        <button
          class="session-main"
          @click="chatStore.selectSession(session.id)"
        >
          <div class="session-header">
            <el-icon
              v-if="session.is_pinned"
              class="pin-icon"
            >
              <StarFilled />
            </el-icon>
            <strong :title="session.title || '新会话'">{{ session.title || "新会话" }}</strong>
          </div>
          <span class="session-time">{{ session.updated_at }}</span>
        </button>

        <div class="session-actions">
          <el-button
            :icon="StarFilled"
            size="small"
            text
            :title="session.is_pinned ? '取消置顶' : '置顶'"
            @click.stop="handleTogglePin(session.id)"
          />
          <el-button
            :icon="Edit"
            size="small"
            text
            title="重命名"
            @click.stop="openRenameDialog(session.id, session.title || '')"
          />
          <el-button
            :icon="Download"
            size="small"
            text
            title="导出"
            @click.stop="openExportDialog(session.id, session.title || '新会话')"
          />
          <el-button
            :icon="Delete"
            size="small"
            text
            title="删除"
            @click.stop="handleDelete(session.id, session.title || '新会话')"
          />
        </div>
      </div>
    </div>

    <SessionRenameDialog
      v-model:visible="renameDialogVisible"
      :session-id="selectedSessionForAction"
      :current-title="selectedSessionTitle"
      @confirm="handleRename"
    />

    <SessionExportDialog
      v-model:visible="exportDialogVisible"
      :session-id="selectedSessionForAction"
      :session-title="selectedSessionTitle"
      @export="handleExport"
    />
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
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: all 0.2s ease;
  position: relative;
}

.session-card:hover {
  border-color: var(--color-earth-400);
  background: rgba(255, 255, 255, 0.9);
}

.session-card.active {
  border-color: var(--color-terracotta-500);
  background: rgba(253, 246, 243, 0.9);
  border-left-width: 3px;
  padding-left: 12px;
}

.session-card.pinned {
  background: rgba(253, 246, 243, 0.7);
}

.session-main {
  width: 100%;
  background: none;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.session-header {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pin-icon {
  color: var(--color-terracotta-500);
  font-size: 12px;
  flex-shrink: 0;
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
  flex: 1;
}

.session-time {
  color: var(--color-earth-600);
  font-size: 11px;
  opacity: 0.8;
}

.session-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.session-card:hover .session-actions {
  opacity: 1;
}

.session-actions .el-button {
  padding: 4px;
  color: var(--color-earth-600);
}

.session-actions .el-button:hover {
  color: var(--color-terracotta-500);
  background: rgba(212, 106, 67, 0.1);
}
</style>
