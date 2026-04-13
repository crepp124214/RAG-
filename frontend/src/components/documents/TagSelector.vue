<script setup lang="ts">
import { ref, computed } from "vue"
import { ElMessage } from "element-plus"
import { useDocumentStore } from "@/stores/documents"
import type { TagData } from "@/services/documents"

const documentStore = useDocumentStore()

const props = defineProps<{
  documentId: string
  currentTags: TagData[]
}>()

const emit = defineEmits<{
  updated: []
  "manage-tags": []
}>()

const selectedTagIds = ref<number[]>(props.currentTags.map((tag) => tag.id))
const isSubmitting = ref(false)

const availableTags = computed(() => documentStore.tags)

const hasChanges = computed(() => {
  const current = new Set(props.currentTags.map((tag) => tag.id))
  const selected = new Set(selectedTagIds.value)

  if (current.size !== selected.size) {
    return true
  }

  for (const id of current) {
    if (!selected.has(id)) {
      return true
    }
  }

  return false
})

async function handleSubmit() {
  if (!hasChanges.value) {
    return
  }

  isSubmitting.value = true

  try {
    await documentStore.setTagsForDocument(props.documentId, selectedTagIds.value)
    ElMessage.success("标签设置成功")
    emit("updated")
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "设置标签失败")
  } finally {
    isSubmitting.value = false
  }
}

function handleCancel() {
  selectedTagIds.value = props.currentTags.map((tag) => tag.id)
}
</script>

<template>
  <div class="tag-selector">
    <div class="tag-selector-header">
      <span class="label">选择标签</span>
      <el-button
        v-if="availableTags.length === 0"
        size="small"
        text
        type="primary"
        @click="$emit('manage-tags')"
      >
        创建标签
      </el-button>
    </div>

    <el-empty
      v-if="availableTags.length === 0"
      description="暂无标签，请先创建标签"
      :image-size="60"
    />

    <div v-else class="tag-options">
      <el-checkbox-group v-model="selectedTagIds">
        <el-checkbox
          v-for="tag in availableTags"
          :key="tag.id"
          :label="tag.id"
          :value="tag.id"
        >
          <el-tag :color="tag.color" effect="dark" size="small">
            {{ tag.name }}
          </el-tag>
        </el-checkbox>
      </el-checkbox-group>
    </div>

    <div v-if="availableTags.length > 0" class="tag-selector-actions">
      <el-button
        type="primary"
        size="small"
        :disabled="!hasChanges"
        :loading="isSubmitting"
        @click="handleSubmit"
      >
        保存
      </el-button>
      <el-button
        size="small"
        :disabled="!hasChanges"
        @click="handleCancel"
      >
        取消
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.tag-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tag-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tag-selector-header .label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-earth-900);
}

.tag-options {
  padding: 12px;
  border-radius: 8px;
  background: rgba(249, 246, 240, 0.6);
  border: 1px solid rgba(201, 184, 154, 0.15);
  max-height: 200px;
  overflow-y: auto;
}

.tag-options :deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tag-options :deep(.el-checkbox) {
  margin-right: 0;
}

.tag-selector-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
