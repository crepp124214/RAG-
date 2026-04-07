<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue"

import { useDocumentStore } from "@/stores/documents"

const documentStore = useDocumentStore()
const fileInputRef = ref<HTMLInputElement | null>(null)

const selectedItem = computed(() => documentStore.selectedItem)

function openFilePicker() {
  fileInputRef.value?.click()
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]

  if (!file) {
    return
  }

  try {
    await documentStore.upload(file)
  } finally {
    input.value = ""
  }
}

async function handleDelete(documentId: string) {
  await documentStore.deleteDocument(documentId)
}

onMounted(() => {
  void documentStore.hydrate()
})

onBeforeUnmount(() => {
  for (const item of documentStore.items) {
    documentStore.stopPolling(item.documentId)
  }
})
</script>

<template>
  <section class="sub-panel support-module-panel">
    <div class="panel-header">
      <div class="panel-copy">
        <p class="support-eyebrow">支持模块</p>
        <h2>知识库支持</h2>
        <span>上传资料、查看最近文档，并快速确认当前知识库上下文。</span>
      </div>
      <el-button
        data-testid="document-support-upload"
        type="primary"
        size="small"
        :loading="documentStore.isUploading"
        @click="openFilePicker"
      >
        上传资料
      </el-button>
      <input
        ref="fileInputRef"
        class="hidden-input"
        type="file"
        accept=".pdf,.docx,.txt"
        @change="handleFileChange"
      />
    </div>

    <el-alert
      v-if="documentStore.uploadError"
      :closable="false"
      type="error"
      show-icon
      title="上传失败"
      :description="documentStore.uploadError"
    />

    <el-alert
      v-else-if="documentStore.actionError"
      :closable="false"
      type="warning"
      show-icon
      title="文档操作异常"
      :description="documentStore.actionError"
    />

    <el-alert
      v-else-if="documentStore.isHydrating"
      :closable="false"
      type="info"
      show-icon
      title="正在恢复文档状态"
      description="页面会根据本地保存的文档清单恢复上传记录和任务状态。"
    />

    <div class="summary-row support-summary-row">
      <el-tag
        type="info"
        size="small"
      >
        已跟踪 {{ documentStore.trackedCount }} 份
      </el-tag>
      <el-tag
        type="warning"
        size="small"
      >
        处理中 {{ documentStore.activeTaskCount }} 份
      </el-tag>
    </div>

    <div class="support-stack">
      <div class="support-block">
        <div class="support-block-header">
          <h3>最近文档</h3>
          <span>保留最近状态，方便聊天时快速切换证据。</span>
        </div>

        <el-empty
          v-if="documentStore.items.length === 0"
          description="还没有已跟踪的文档，请先上传 PDF、DOCX 或 TXT 文件。"
        />

        <div
          v-else
          class="recent-document-list"
        >
          <button
            v-for="item in documentStore.items"
            :key="item.documentId"
            data-testid="recent-document-item"
            class="document-card"
            :class="{ active: item.documentId === documentStore.selectedDocumentId }"
            @click="documentStore.setSelectedDocument(item.documentId)"
          >
            <div class="document-card-top">
              <strong>{{ item.name }}</strong>
              <el-tag
                size="small"
                effect="plain"
              >
                {{ item.fileType }}
              </el-tag>
            </div>
            <div class="document-card-meta">
              <span>文档 {{ item.documentStatus }}</span>
              <span>任务 {{ item.taskStatus }}</span>
              <span>图谱 {{ item.graphStatus }}</span>
            </div>
          </button>
        </div>
      </div>

      <div class="support-block document-detail">
        <div class="support-block-header">
          <h3>当前选中</h3>
          <span>仅保留聊天前需要确认的关键信息。</span>
        </div>

        <el-empty
          v-if="!selectedItem"
          description="选中文档后，这里会显示详情、任务状态和失败原因。"
        />

        <template v-else>
          <div class="detail-header">
            <div data-testid="selected-document-detail">
              <h3>{{ selectedItem.name }}</h3>
              <p>文档 ID：{{ selectedItem.documentId }}</p>
            </div>
            <el-button
              data-testid="delete-document-action"
              type="danger"
              plain
              size="small"
              @click="handleDelete(selectedItem.documentId)"
            >
              删除文档
            </el-button>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <span>文件类型</span>
              <strong>{{ selectedItem.fileType }}</strong>
            </div>
            <div class="detail-item">
              <span>文档状态</span>
              <strong>{{ selectedItem.documentStatus }}</strong>
            </div>
            <div class="detail-item">
              <span>任务状态</span>
              <strong>{{ selectedItem.taskStatus }}</strong>
            </div>
            <div class="detail-item">
              <span>视觉资产</span>
              <strong>{{ selectedItem.visualAssetCount }}</strong>
            </div>
            <div class="detail-item">
              <span>任务类型</span>
              <strong>{{ selectedItem.taskType }}</strong>
            </div>
            <div class="detail-item">
              <span>图谱状态</span>
              <strong data-testid="selected-graph-status">{{ selectedItem.graphStatus }}</strong>
            </div>
            <div class="detail-item">
              <span>图谱关系</span>
              <strong data-testid="selected-graph-relations">{{ selectedItem.graphRelationCount }}</strong>
            </div>
          </div>

          <el-alert
            v-if="selectedItem.hasGraph"
            :closable="false"
            type="info"
            show-icon
            title="图谱构建已就绪"
            :description="`当前文档已构建 ${selectedItem.graphRelationCount} 条图谱关系，可用于关系型问答。`"
          />

          <el-alert
            v-else-if="selectedItem.graphStatus === 'FAILED'"
            :closable="false"
            type="warning"
            show-icon
            title="图谱构建失败"
            description="文本问答仍可继续使用，但当前文档暂时无法提供图谱证据。"
          />

          <el-alert
            v-if="selectedItem.hasVisualAssets"
            :closable="false"
            type="success"
            show-icon
            title="已生成视觉描述"
            :description="`当前文档已提取 ${selectedItem.visualAssetCount} 条视觉资产，可用于图表和图片相关问答。`"
          />

          <el-alert
            v-if="selectedItem.errorMessage"
            :closable="false"
            type="error"
            show-icon
            title="任务失败"
            :description="selectedItem.errorMessage"
          />

          <p class="detail-timestamp">
            最后更新时间：{{ selectedItem.updatedAt }}
          </p>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hidden-input {
  display: none;
}

.support-module-panel {
  gap: 14px;
}

.panel-copy {
  display: grid;
  gap: 4px;
}

.panel-copy h2,
.support-block-header h3 {
  margin: 0;
}

.support-eyebrow {
  margin: 0;
  color: #0f766e;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.support-summary-row {
  margin-top: 4px;
}

.support-stack,
.document-detail {
  display: grid;
  gap: 10px;
}

.support-block {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.9);
  padding: 14px;
}

.support-block-header {
  display: grid;
  gap: 4px;
}

.support-block-header span {
  color: #64748b;
  font-size: 12px;
}

.recent-document-list {
  display: grid;
  gap: 8px;
}

.summary-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.document-card {
  width: 100%;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 14px;
  background: #ffffff;
  padding: 12px;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.document-card:hover,
.document-card.active {
  border-color: rgba(15, 118, 110, 0.45);
  transform: translateY(-1px);
  box-shadow: 0 10px 24px rgba(148, 163, 184, 0.14);
}

.document-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.document-card-meta {
  display: grid;
  gap: 4px;
  color: #475569;
  font-size: 13px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.detail-header h3,
.detail-header p {
  margin: 0;
}

.detail-header p {
  margin-top: 6px;
  color: #64748b;
  font-size: 13px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.detail-item {
  padding: 10px 12px;
  border-radius: 12px;
  background: #f8fafc;
  display: grid;
  gap: 4px;
}

.detail-item span,
.detail-timestamp {
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 900px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .detail-header {
    flex-direction: column;
  }
}
</style>
