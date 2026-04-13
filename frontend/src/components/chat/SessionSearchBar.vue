<script setup lang="ts">
import { ref, watch } from "vue"
import { Search } from "@element-plus/icons-vue"

interface Props {
  modelValue: string
}

interface Emits {
  (e: "update:modelValue", value: string): void
  (e: "search", keyword: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localValue = ref(props.modelValue)

watch(
  () => props.modelValue,
  (newValue) => {
    localValue.value = newValue
  },
)

function handleInput(value: string) {
  localValue.value = value
  emit("update:modelValue", value)
  emit("search", value)
}

function handleClear() {
  localValue.value = ""
  emit("update:modelValue", "")
  emit("search", "")
}
</script>

<template>
  <el-input
    :model-value="localValue"
    placeholder="搜索会话..."
    :prefix-icon="Search"
    clearable
    @input="handleInput"
    @clear="handleClear"
    class="session-search-bar"
  />
</template>

<style scoped>
.session-search-bar {
  width: 100%;
}

.session-search-bar :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(201, 184, 154, 0.3);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.session-search-bar :deep(.el-input__wrapper:hover) {
  border-color: var(--color-earth-400);
  background: rgba(255, 255, 255, 0.95);
}

.session-search-bar :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-terracotta-500);
  box-shadow: 0 0 0 2px rgba(212, 106, 67, 0.1);
}
</style>
