<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue"

import { useDocumentStore } from "@/stores/documents"
import DocumentSearch from "./DocumentSearch.vue"
import DocumentBatchActions from "./DocumentBatchActions.vue"
import TagManager from "./TagManager.vue"
import TagSelector from "./TagSelector.vue"
import DocumentPreview from "./DocumentPreview.vue"

const documentStore = useDocumentStore()
const fileInputRef = ref<HTMLInputElement | null>(null)
const showTagManager = ref(false)
const showTagSelector = ref(false)
const showPreview = ref(false)
const previewDocumentId = ref<string | null>(null)

const selectedItem = computed(() => documentStore.selectedItem)
const filteredItems = computed(() => documentStore.filteredItems)

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

function openTagManager() {
  showTagManager.value = true
}

function openTagSelector() {
  showTagSelector.value = true
}

function openPreview(documentId: string) {
  previewDocumentId.value = documentId
  showPreview.value = true
}

function handleTagUpdated() {
  showTagSelector.value = false
}

onMounted(() => {
  void documentStore.hydrate()
  void documentStore.loadTags()
})

onBeforeUnmount(() => {
  for (const item of documentStore.items) {
    documentStore.stopPolling(item.documentId)
  }
})
</script>

<template>
  <section class="document-panel">
    <div class="panel-header">
      <h3>知识库</h3>
      <div class="header-actions">
        <el-button size="small" @click="openTagManager">
          标签管理
        </el-button>
        <el-button
          data-testid="document-support-upload"
          type="primary"
          size="small"
          :loading="documentStore.isUploading"
          @click="openFilePicker"
        >
          上传
        </el-button>
      </div>
      <input
        ref="fileInputRef"
        class="hidden-input"
        type="file"
        accept=".pdf,.docx,.txt"
        @change="handleFileChange"
      >
    </div>

    <el-alert
      v-if="documentStore.uploadError"
      :closable="false"
      type="error"
      show-icon
      :description="documentStore.uploadError"
    ></el-alert>

    <el-alert
      v-else-if="documentStore.actionError"
      :closable="false"
      type="warning"
      show-icon
      :description="documentStore.actionError"
    ></el-alert>

    <DocumentSearch @manage-tags="openTagManager"></DocumentSearch>

    <DocumentBatchActions></DocumentBatchActions>

    <div class="summary-tags">
      <el-tag type="info" size="small">
        已跟踪 {{ documentStore.trackedCount }}
      </el-tag>
      <el-tag type="warning" size="small">
        处理中 {{ documentStore.activeTaskCount }}
      </el-tag>
    </div>

    <el-empty
      v-if="filteredItems.length === 0"
      description="暂无文档"
    ></el-empty>

    <div v-else class="document-list">
      <button
        v-for="item in filteredItems"
        :key="item.documentId"
        data-testid="recent-document-item"
        class="document-card"
        :class="{ active: item.documentId === documentStore.selectedDocumentId }"
        @click="documentStore.setSelectedDocument(item.documentId)"
      >
        <div class="doc-header">
          <el-checkbox
            :model-value="documentStore.selectedDocuments.has(item.documentId)"
            @click.stop
            @change="documentStore.toggleDocumentSelection(item.documentId)"
          ></el-checkbox>
          <strong>{{ item.name }}</strong>
          <el-tag size="small" effect="plain">{{ item.fileType }}</el-tag>
        </div>
        <div class="doc-meta">
          <span>{{ item.taskStatus }}</span>
          <span v-if="item.graphStatus !== 'NONE'">图谱: {{ item.graphStatus }}</span>
        </div>
        <div v-if="item.tags.length > 0" class="doc-tags">
          <el-tag
            v-for="tag in item.tags"
            :key="tag.id"
            :color="tag.color"
            effect="dark"
            size="small"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </button>
    </div>

    <div v-if="selectedItem" class="document-detail">
      <div class="detail-header">
        <h4>{{ selectedItem.name }}</h4>
        <div class="detail-actions">
          <el-button size="small" @click="openPreview(selectedItem.documentId)">
            预览
          </el-button>
          <el-button size="small" @click="openTagSelector">
            标签
          </el-button>
          <el-button
            data-testid="delete-document-action"
            type="danger"
            plain
            size="small"
            @click="handleDelete(selectedItem.documentId)"
          >
            删除
          </el-button>
        </div>
      </div>

      <div class="detail-grid">
        <div class="detail-item">
          <span>状态</span>
          <strong>{{ selectedItem.taskStatus }}</strong>
        </div>
        <div class="detail-item">
          <span>类型</span>
          <strong>{{ selectedItem.fileType }}</strong>
        </div>
        <div v-if="selectedItem.graphRelationCount > 0" class="detail-item">
          <span>图谱关系</span>
          <strong data-testid="selected-graph-relations">{{ selectedItem.graphRelationCount }}</strong>
        </div>
        <div v-if="selectedItem.visualAssetCount > 0" class="detail-item">
          <span>视觉资产</span>
          <strong>{{ selectedItem.visualAssetCount }}</strong>
        </div>
      </div>

      <div v-if="selectedItem.tags.length > 0" class="detail-tags">
        <span class="tags-label">标签：</span>
        <div class="tags-list">
          <el-tag
            v-for="tag in selectedItem.tags"
            :key="tag.id"
            :color="tag.color"
            effect="dark"
            size="small"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>

      <el-alert
        v-if="selectedItem.errorMessage"
        :closable="false"
        type="error"
        show-icon
        :description="selectedItem.errorMessage"
      ></el-alert>

      <TagSelector
        v-if="showTagSelector"
        :document-id="selectedItem.documentId"
        :current-tags="selectedItem.tags"
        @updated="handleTagUpdated"
        @manage-tags="openTagManager"
      ></TagSelector>
    </div>

    <TagManager v-model:visible="showTagManager"></TagManager>
    <DocumentPreview
      v-model:visible="showPreview"
      :document-id="previewDocumentId"
    ></DocumentPreview>
  </section>
</template>

<style scoped>
.hidden-input {
  display: none;
}

.document-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.header-actions {
  display: flex;
  gap: 8px;
}

.summary-tags {
  display: flex;
  gap: 8px;
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.document-card {
  width: 100%;
  border: 1px solid rgba(201, 184, 154, 0.2);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.6);
  padding: 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.document-card:hover {
  border-color: var(--color-earth-400);
  background: rgba(255, 255, 255, 0.9);
  transform: translateY(-1px);
}

.document-card.active {
  border-color: var(--color-moss-500);
  background: rgba(246, 248, 244, 0.9);
  border-left-width: 3px;
  padding-left: 10px;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.doc-header :deep(.el-checkbox) {
  margin-right: 8px;
}

.doc-header strong {
  font-family: "LXGW WenKai", serif;
  font-weight: 600;
  color: var(--color-earth-900);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.doc-meta {
  display: flex;
  gap: 8px;
  color: var(--color-earth-600);
  font-size: 11px;
}

.doc-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.document-detail {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid rgba(201, 184, 154, 0.15);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.detail-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-header h4 {
  margin: 0;
  font-size: 14px;
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  color: var(--color-earth-900);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.detail-item {
  padding: 10px;
  border-radius: 8px;
  background: rgba(249, 246, 240, 0.6);
  border: 1px solid rgba(201, 184, 154, 0.15);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item span {
  color: var(--color-earth-600);
  font-size: 11px;
}

.detail-item strong {
  color: var(--color-earth-900);
  font-size: 13px;
  font-weight: 600;
}

.detail-tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tags-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-earth-700);
}

.tags-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .header-actions {
    justify-content: flex-end;
  }

  .detail-header {
    flex-direction: column;
    align-items: stretch;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
