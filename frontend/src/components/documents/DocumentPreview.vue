<script setup lang="ts">
import { computed, watch } from "vue"
import { useDocumentStore } from "@/stores/documents"

const documentStore = useDocumentStore()

const props = defineProps<{
  visible: boolean
  documentId: string | null
}>()

const emit = defineEmits<{
  "update:visible": [value: boolean]
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
})

watch(
  () => [props.visible, props.documentId],
  async ([visible, documentId]) => {
    if (visible && documentId) {
      await documentStore.loadDocumentPreview(documentId)
    } else if (!visible) {
      documentStore.clearDocumentPreview()
    }
  },
  { immediate: true },
)
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="文档预览"
    width="800px"
    :close-on-click-modal="false"
    destroy-on-close
  >
    <div class="document-preview">
      <el-skeleton v-if="documentStore.isLoadingPreview" :rows="6" animated />

      <template v-else-if="documentStore.previewData">
        <div class="preview-header">
          <h3>{{ documentStore.previewData.document_name }}</h3>
          <el-tag type="info">
            共 {{ documentStore.previewData.total_chunks }} 个分块，显示前 {{ documentStore.previewData.chunks.length }} 个
          </el-tag>
        </div>

        <el-empty
          v-if="documentStore.previewData.chunks.length === 0"
          description="该文档暂无可预览内容"
        />

        <div v-else class="preview-chunks">
          <div
            v-for="chunk in documentStore.previewData.chunks"
            :key="chunk.id"
            class="chunk-card"
          >
            <div class="chunk-header">
              <el-tag size="small" effect="plain">
                分块 {{ chunk.chunk_index + 1 }}
              </el-tag>
            </div>
            <div class="chunk-content">
              {{ chunk.content }}
            </div>
          </div>
        </div>
      </template>

      <el-empty v-else description="暂无预览数据" />
    </div>
  </el-dialog>
</template>

<style scoped>
.document-preview {
  min-height: 200px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(201, 184, 154, 0.15);
}

.preview-header h3 {
  margin: 0;
  font-size: 16px;
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  color: var(--color-earth-900);
}

.preview-chunks {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 500px;
  overflow-y: auto;
}

.chunk-card {
  padding: 16px;
  border-radius: 10px;
  background: rgba(249, 246, 240, 0.6);
  border: 1px solid rgba(201, 184, 154, 0.15);
}

.chunk-header {
  margin-bottom: 12px;
}

.chunk-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--color-earth-800);
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 768px) {
  .preview-header {
    flex-direction: column;
  }
}
</style>
