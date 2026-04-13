<script setup lang="ts">
import { ref, computed } from "vue"
import { Search } from "@element-plus/icons-vue"
import { useDocumentStore } from "@/stores/documents"

const documentStore = useDocumentStore()

const searchInput = ref(documentStore.searchKeyword)
const selectedTagIds = ref<number[]>([...documentStore.selectedTags])

const emit = defineEmits<{
  "manage-tags": []
}>()

const hasActiveFilters = computed(() => {
  return searchInput.value.length > 0 || selectedTagIds.value.length > 0
})

function handleSearch() {
  documentStore.setSearchKeyword(searchInput.value)
  documentStore.setSelectedTags(selectedTagIds.value)
}

function handleClear() {
  searchInput.value = ""
  selectedTagIds.value = []
  documentStore.clearFilters()
}

function handleTagChange() {
  documentStore.setSelectedTags(selectedTagIds.value)
}
</script>

<template>
  <div class="document-search">
    <div class="search-input-wrapper">
      <el-input
        v-model="searchInput"
        placeholder="搜索文档名称..."
        clearable
        @keyup.enter="handleSearch"
        @clear="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="handleSearch">
        搜索
      </el-button>
    </div>

    <div class="filter-section">
      <div class="filter-header">
        <span class="filter-label">按标签筛选</span>
        <el-button
          size="small"
          text
          type="primary"
          @click="emit('manage-tags')"
        >
          管理标签
        </el-button>
      </div>

      <el-select
        v-model="selectedTagIds"
        multiple
        collapse-tags
        collapse-tags-tooltip
        placeholder="选择标签"
        style="width: 100%"
        @change="handleTagChange"
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

    <div v-if="hasActiveFilters" class="filter-summary">
      <span class="summary-text">
        已筛选 {{ documentStore.filteredItems.length }} / {{ documentStore.trackedCount }} 个文档
      </span>
      <el-button size="small" text @click="handleClear">
        清除筛选
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.document-search {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(249, 246, 240, 0.6);
  border: 1px solid rgba(201, 184, 154, 0.15);
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-earth-700);
}

.filter-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid rgba(201, 184, 154, 0.15);
}

.summary-text {
  font-size: 12px;
  color: var(--color-earth-600);
}
</style>
