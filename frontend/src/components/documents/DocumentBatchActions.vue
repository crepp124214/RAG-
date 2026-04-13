<script setup lang="ts">
import { ref, computed } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { useDocumentStore } from "@/stores/documents"

const documentStore = useDocumentStore()

const showTagSelector = ref(false)
const selectedTagIds = ref<number[]>([])
const isProcessing = ref(false)

const hasSelection = computed(() => documentStore.hasSelectedDocuments)
const selectionCount = computed(() => documentStore.selectedDocumentsCount)
const allSelected = computed(() => {
  return (
    documentStore.filteredItems.length > 0 &&
    documentStore.selectedDocumentsCount === documentStore.filteredItems.length
  )
})

function handleSelectAll() {
  if (allSelected.value) {
    documentStore.clearDocumentSelection()
  } else {
    documentStore.selectAllFilteredDocuments()
  }
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectionCount.value} 个文档吗？此操作不可恢复。`,
      "确认批量删除",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    )

    isProcessing.value = true
    await documentStore.batchDeleteSelectedDocuments()
    ElMessage.success("批量删除成功")
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error instanceof Error ? error.message : "批量删除失败")
    }
  } finally {
    isProcessing.value = false
  }
}

function openTagSelector() {
  selectedTagIds.value = []
  showTagSelector.value = true
}

async function handleBatchTag() {
  if (selectedTagIds.value.length === 0) {
    ElMessage.warning("请至少选择一个标签")
    return
  }

  isProcessing.value = true

  try {
    await documentStore.batchTagSelectedDocuments(selectedTagIds.value)
    ElMessage.success("批量设置标签成功")
    showTagSelector.value = false
    selectedTagIds.value = []
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "批量设置标签失败")
  } finally {
    isProcessing.value = false
  }
}
</script>

<template>
  <div class="batch-actions">
    <div class="batch-header">
      <el-checkbox
        :model-value="allSelected"
        :indeterminate="hasSelection && !allSelected"
        @change="handleSelectAll"
      >
        全选
      </el-checkbox>
      <span v-if="hasSelection" class="selection-count">
        已选择 {{ selectionCount }} 个文档
      </span>
    </div>

    <div v-if="hasSelection" class="action-buttons">
      <el-button
        size="small"
        type="primary"
        :loading="isProcessing"
        @click="openTagSelector"
      >
        批量打标签
      </el-button>
      <el-button
        size="small"
        type="danger"
        :loading="isProcessing"
        @click="handleBatchDelete"
      >
        批量删除
      </el-button>
      <el-button
        size="small"
        @click="documentStore.clearDocumentSelection"
      >
        取消选择
      </el-button>
    </div>

    <el-dialog
      v-model="showTagSelector"
      title="批量设置标签"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="batch-tag-dialog">
        <p class="dialog-hint">
          将为选中的 {{ selectionCount }} 个文档设置以下标签（会覆盖原有标签）：
        </p>

        <el-select
          v-model="selectedTagIds"
          multiple
          placeholder="选择标签"
          style="width: 100%"
        >
          <el-option
            v-for="tag in documentStore.tags"
            :key="tag.id"
            :label="tag.name"
            :value="tag.id"
          >
            <el-tag :color="tag.color" effect="dark" size="small">
              {{ tag.name }}
            </el-tag>
          </el-option>
        </el-select>
      </div>

      <template #footer>
        <el-button @click="showTagSelector = false">取消</el-button>
        <el-button
          type="primary"
          :loading="isProcessing"
          @click="handleBatchTag"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.batch-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(246, 248, 244, 0.9);
  border: 1px solid rgba(201, 184, 154, 0.2);
}

.batch-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selection-count {
  font-size: 12px;
  color: var(--color-earth-600);
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.batch-tag-dialog {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-earth-700);
  line-height: 1.5;
}
</style>
