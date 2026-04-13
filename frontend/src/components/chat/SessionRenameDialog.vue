<script setup lang="ts">
import { ref, watch } from "vue"
import { ElMessage } from "element-plus"

interface Props {
  visible: boolean
  sessionId: string | null
  currentTitle: string
}

interface Emits {
  (e: "update:visible", value: boolean): void
  (e: "confirm", sessionId: string, newTitle: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const newTitle = ref("")
const isSubmitting = ref(false)

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      newTitle.value = props.currentTitle
    }
  },
)

function handleClose() {
  emit("update:visible", false)
  newTitle.value = ""
}

async function handleConfirm() {
  const trimmedTitle = newTitle.value.trim()

  if (!trimmedTitle) {
    ElMessage.warning("会话标题不能为空")
    return
  }

  if (trimmedTitle.length > 200) {
    ElMessage.warning("会话标题不能超过 200 个字符")
    return
  }

  if (!props.sessionId) {
    ElMessage.error("会话 ID 无效")
    return
  }

  isSubmitting.value = true

  try {
    emit("confirm", props.sessionId, trimmedTitle)
    handleClose()
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="重命名会话"
    width="500px"
    @close="handleClose"
  >
    <el-form @submit.prevent="handleConfirm">
      <el-form-item label="会话标题">
        <el-input
          v-model="newTitle"
          placeholder="请输入会话标题"
          maxlength="200"
          show-word-limit
          :disabled="isSubmitting"
          autofocus
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button
        @click="handleClose"
        :disabled="isSubmitting"
      >
        取消
      </el-button>
      <el-button
        type="primary"
        @click="handleConfirm"
        :loading="isSubmitting"
      >
        确定
      </el-button>
    </template>
  </el-dialog>
</template>
