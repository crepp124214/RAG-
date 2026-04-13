<script setup lang="ts">
import { ref } from "vue"
import { ElMessage } from "element-plus"
import { Download } from "@element-plus/icons-vue"

interface Props {
  visible: boolean
  sessionId: string | null
  sessionTitle: string
}

interface Emits {
  (e: "update:visible", value: boolean): void
  (e: "export", sessionId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const isExporting = ref(false)

function handleClose() {
  emit("update:visible", false)
}

async function handleExport() {
  if (!props.sessionId) {
    ElMessage.error("会话 ID 无效")
    return
  }

  isExporting.value = true

  try {
    emit("export", props.sessionId)
  } finally {
    isExporting.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="导出会话"
    width="500px"
    @close="handleClose"
  >
    <div class="export-info">
      <p>
        <strong>会话标题：</strong>{{ sessionTitle }}
      </p>
      <p class="export-hint">
        会话将导出为 Markdown 格式，包含所有消息内容、引用和工具调用记录。
      </p>
    </div>

    <template #footer>
      <el-button
        @click="handleClose"
        :disabled="isExporting"
      >
        取消
      </el-button>
      <el-button
        type="primary"
        :icon="Download"
        @click="handleExport"
        :loading="isExporting"
      >
        导出
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.export-info {
  padding: 12px 0;
}

.export-info p {
  margin: 8px 0;
  color: var(--color-earth-800);
  font-size: 14px;
  line-height: 1.6;
}

.export-info strong {
  color: var(--color-earth-900);
  font-weight: 600;
}

.export-hint {
  margin-top: 16px;
  padding: 12px;
  background: rgba(253, 246, 243, 0.6);
  border-left: 3px solid var(--color-terracotta-500);
  border-radius: 4px;
  font-size: 13px;
  color: var(--color-earth-700);
}
</style>
