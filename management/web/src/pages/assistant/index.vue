<script lang="ts" setup>
import { Star, Delete, Plus, Refresh, Setting } from "@element-plus/icons-vue"
import axios from "axios"

defineOptions({
  name: "ModelManagement"
})

// 模型数据类型
interface ModelData {
  id: string
  llm_name: string
  llm_factory: string
  model_type: string
  api_key: string
  api_base: string
  enabled: boolean
  create_time: string
  update_time: string
  is_default?: boolean
}

// 状态
const loading = ref(false)
const modelList = ref<ModelData[]>([])
const defaultModelId = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchName = ref("")

// 配置对话框状态
const configDialogVisible = ref(false)
const configDialogTitle = ref("配置模型")
const isEdit = ref(false)
const saving = ref(false)

// 当前编辑的模型数据
const currentModel = ref<Partial<ModelData>>({
  llm_name: "",
  llm_factory: "",
  model_type: "chat",
  api_key: "",
  api_base: "",
  enabled: true
})

/**
 * 获取模型列表
 */
async function getModelList() {
  loading.value = true
  try {
    const response = await axios.get("/api/v1/dialog/llms")
    if (response.data.code === 0) {
      modelList.value = response.data.data || []
      total.value = modelList.value.length
      
      // 标记默认模型
      modelList.value.forEach((item) => {
        item.is_default = item.llm_name === defaultModelId.value
      })
    }
  } catch (error) {
    console.error("获取模型列表失败:", error)
    ElMessage.error("获取模型列表失败")
  } finally {
    loading.value = false
  }
}

/**
 * 获取默认模型ID
 */
async function getDefaultModel() {
  try {
    const response = await axios.get("/api/v1/model/default")
    if (response.data.code === 0) {
      defaultModelId.value = response.data.data.model_id
    }
  } catch (error) {
    console.error("获取默认模型失败:", error)
  }
}

/**
 * 搜索
 */
function handleSearch() {
  currentPage.value = 1
  getModelList()
}

/**
 * 刷新
 */
function handleRefresh() {
  searchName.value = ""
  currentPage.value = 1
  getModelList()
}

/**
 * 分页变化
 */
function handlePageChange(page: number) {
  currentPage.value = page
  getModelList()
}

/**
 * 显示配置对话框
 */
function showConfigDialog(row: ModelData) {
  configDialogTitle.value = "模型详情"
  isEdit.value = true
  currentModel.value = {
    ...row
  }
  configDialogVisible.value = true
}

/**
 * 设置默认模型
 */
async function handleSetDefault(row: ModelData) {
  try {
    await axios.post(`/api/v1/model/${row.llm_name}/set-default`)
    defaultModelId.value = row.llm_name
    ElMessage.success("设置成功")
    getModelList()
  } catch (error) {
    console.error("设置默认模型失败:", error)
    ElMessage.error("设置失败")
  }
}

/**
 * 格式化时间
 */
function formatTime(time: string) {
  if (!time) return ""
  return new Date(time).toLocaleString()
}

// 初始化
onMounted(async () => {
  await getDefaultModel()
  await getModelList()
})
</script>

<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-card shadow="hover" class="search-wrapper">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input v-model="searchName" placeholder="请输入模型名称" clearable @keyup.enter="handleSearch" />
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleRefresh">
            重置
          </el-button>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-text type="info">
            可用模型列表（模型需在系统设置中配置API Key）
          </el-text>
        </el-col>
      </el-row>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="hover" class="table-wrapper">
      <el-table v-loading="loading" :data="modelList" border stripe>
        <el-table-column label="默认" width="70" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.is_default" color="#f7ba2a" :size="20">
              <Star />
            </el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="llm_name" label="模型名称" min-width="200" />
        <el-table-column prop="llm_factory" label="模型厂商" min-width="150">
          <template #default="{ row }">
            {{ row.fid || row.llm_factory || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="model_type" label="模型类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.model_type === 'chat' ? 'success' : 'info'">
              {{ row.model_type === 'chat' ? '对话' : row.model_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_default"
              type="warning"
              size="small"
              :icon="Star"
              @click="handleSetDefault(row)"
            >
              设为默认
            </el-button>
            <el-button type="primary" size="small" :icon="Setting" @click="showConfigDialog(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        class="pagination"
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      :title="configDialogTitle"
      width="500px"
      destroy-on-close
    >
      <el-form :model="currentModel" label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="currentModel.llm_name" disabled />
        </el-form-item>
        <el-form-item label="模型厂商">
          <el-input :value="currentModel.fid || currentModel.llm_factory" disabled />
        </el-form-item>
        <el-form-item label="模型类型">
          <el-tag :type="currentModel.model_type === 'chat' ? 'success' : 'info'">
            {{ currentModel.model_type === 'chat' ? '对话模型' : currentModel.model_type }}
          </el-tag>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="configDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.search-wrapper {
  margin-bottom: 20px;
}

.table-wrapper {
  :deep(.el-card__body) {
    padding-bottom: 10px;
  }
}

.pagination {
  margin-top: 20px;
  justify-content: center;
}

.tip-text {
  color: #909399;
  font-size: 12px;
  margin-left: 10px;
}
</style>
