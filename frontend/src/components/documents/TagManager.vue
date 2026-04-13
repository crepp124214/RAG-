<script setup lang="ts">
import { ref, computed } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { useDocumentStore } from "@/stores/documents"
import type { TagData } from "@/services/documents"

const documentStore = useDocumentStore()

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  "update:visible": [value: boolean]
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
})

const editingTag = ref<TagData | null>(null)
const tagName = ref("")
const tagColor = ref("#409EFF")
const isSubmitting = ref(false)

const predefinedColors = [
  "#409EFF",
  "#67C23A",
  "#E6A23C",
  "#F56C6C",
  "#909399",
  "#00D7FF",
  "#FF6B9D",
  "#C990C0",
  "#FFB800",
  "#94D82D",
]

function startEdit(tag: TagData) {
  editingTag.value = tag
  tagName.value = tag.name
  tagColor.value = tag.color
}

function cancelEdit() {
  editingTag.value = null
  tagName.value = ""
  tagColor.value = "#409EFF"
}

async function handleSubmit() {
  if (!tagName.value.trim()) {
    ElMessage.warning("请输入标签名称")
    return
  }

  isSubmitting.value = true

  try {
    if (editingTag.value) {
      await documentStore.updateExistingTag(editingTag.value.id, tagName.value.trim(), tagColor.value)
      ElMessage.success("标签更新成功")
    } else {
      await documentStore.createNewTag(tagName.value.trim(), tagColor.value)
      ElMessage.success("标签创建成功")
    }
    cancelEdit()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "操作失败")
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete(tag: TagData) {
  try {
    await ElMessageBox.confirm(`确定要删除标签"${tag.name}"吗？删除后将自动解除所有文档的该标签关联。`, "确认删除", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    })

    await documentStore.deleteExistingTag(tag.id)
    ElMessage.success("标签删除成功")
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error(error instanceof Error ? error.message : "删除失败")
    }
  }
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="标签管理"
    width="90%"
    :close-on-click-modal="false"
    :style="{ maxWidth: '600px' }"
  >
    <div class="tag-manager">
      <div class="tag-form">
        <el-form @submit.prevent="handleSubmit">
          <el-form-item label="标签名称">
            <el-input
              v-model="tagName"
              placeholder="请输入标签名称"
              maxlength="50"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="标签颜色">
            <div class="color-picker-wrapper">
              <el-color-picker v-model="tagColor" />
              <div class="predefined-colors">
                <button
                  v-for="color in predefinedColors"
                  :key="color"
                  type="button"
                  class="color-button"
                  :style="{ backgroundColor: color }"
                  :class="{ active: tagColor === color }"
                  @click="tagColor = color"
                />
              </div>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="isSubmitting"
              @click="handleSubmit"
            >
              {{ editingTag ? "更新" : "创建" }}
            </el-button>
            <el-button v-if="editingTag" @click="cancelEdit">
              取消
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-divider />

      <div class="tag-list">
        <h4>已有标签</h4>
        <el-empty v-if="documentStore.tags.length === 0" description="暂无标签" />
        <div v-else class="tag-items">
          <div
            v-for="tag in documentStore.tags"
            :key="tag.id"
            class="tag-item"
          >
            <el-tag :color="tag.color" effect="dark" size="large">
              {{ tag.name }}
            </el-tag>
            <div class="tag-actions">
              <el-button
                size="small"
                text
                @click="startEdit(tag)"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                text
                @click="handleDelete(tag)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style scoped>
.tag-manager {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 60vh;
  overflow-y: auto;
}

.tag-form {
  padding: 8px 0;
}

.color-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 16px;
}

.predefined-colors {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-button {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
}

.color-button:hover {
  transform: scale(1.1);
}

.color-button.active {
  border-color: var(--color-earth-900);
  box-shadow: 0 0 0 2px rgba(201, 184, 154, 0.3);
}

.tag-list h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-family: "Fraunces", "LXGW WenKai", serif;
  font-weight: 600;
  color: var(--color-earth-900);
}

.tag-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(249, 246, 240, 0.6);
  border: 1px solid rgba(201, 184, 154, 0.15);
}

.tag-actions {
  display: flex;
  gap: 4px;
}
</style>
