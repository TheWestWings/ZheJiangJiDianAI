<script lang="ts" setup>
import { Refresh, Plus, Edit, Delete } from "@element-plus/icons-vue"
import axios from "axios"
import { getAllRolesApi, type RoleData } from "@@/apis/roles"

defineOptions({
  name: "ModelManagement"
})

// 模型数据类型
interface ModelData {
  llm_name: string
  llm_factory: string
  model_type: string
  api_base: string
  api_key?: string
  global_enabled: boolean
}

// 状态
const loading = ref(false)
const modelList = ref<ModelData[]>([])
const allModels = ref<ModelData[]>([]) // 存储所有模型用于分页
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchName = ref("")

// 多选状态
const multipleSelection = ref<ModelData[]>([])
const tableRef = ref()

// 编辑对话框状态
const editDialogVisible = ref(false)
const editDialogTitle = ref("新增模型")
const isEditing = ref(false)
const editForm = ref<Partial<ModelData>>({
  llm_name: "",
  llm_factory: "OpenAI-API-Compatible",
  model_type: "chat",
  api_base: "",
  api_key: "",
  global_enabled: true
})

// 表单规则
const editFormRules = {
  llm_name: [{ required: true, message: "请输入模型名称", trigger: "blur" }],
  llm_factory: [{ required: true, message: "请选择模型厂商", trigger: "change" }],
  api_base: [{ required: true, message: "请输入 API Base URL", trigger: "blur" }],
  api_key: [{ required: true, message: "请输入 API Key", trigger: "blur" }]
}

const editFormRef = ref()

/**
 * 获取模型列表（含启用状态）
 */
async function getModelList() {
  loading.value = true
  try {
    const response = await axios.get("/api/v1/dialog/models")
    if (response.data.code === 0) {
      let models = response.data.data || []
      
      // 搜索过滤
      if (searchName.value) {
        models = models.filter((m: ModelData) => 
          m.llm_name.toLowerCase().includes(searchName.value.toLowerCase())
        )
      }
      
      allModels.value = models
      total.value = models.length
      
      // 分页处理
      updatePageData()
    }
  } catch (error) {
    console.error("获取模型列表失败:", error)
    ElMessage.error("获取模型列表失败")
  } finally {
    loading.value = false
  }
}

/**
 * 更新当前页数据
 */
function updatePageData() {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  modelList.value = allModels.value.slice(start, end)
  // 清空选择
  multipleSelection.value = []
}

/**
 * 切换模型启用状态
 */
async function handleToggleEnabled(row: ModelData) {
  try {
    const endpoint = row.global_enabled ? "/api/v1/dialog/model/enable" : "/api/v1/dialog/model/disable"
    const response = await axios.post(endpoint, {
      llm_name: row.llm_name,
      llm_factory: row.llm_factory
    })
    
    if (response.data.code === 0) {
      ElMessage.success(row.global_enabled ? "模型已启用" : "模型已禁用")
    } else {
      row.global_enabled = !row.global_enabled
      ElMessage.error(response.data.message || "操作失败")
    }
  } catch (error) {
    row.global_enabled = !row.global_enabled
    console.error("切换模型状态失败:", error)
    ElMessage.error("操作失败")
  }
}

/**
 * 表格多选事件
 */
function handleSelectionChange(selection: ModelData[]) {
  multipleSelection.value = selection
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
  updatePageData()
}

/**
 * 每页条数变化
 */
function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  updatePageData()
}

/**
 * 显示新增模型对话框
 */
function showAddDialog() {
  editDialogTitle.value = "新增模型"
  isEditing.value = false
  editForm.value = {
    llm_name: "",
    llm_factory: "OpenAI-API-Compatible",
    model_type: "chat",
    api_base: "",
    api_key: "",
    global_enabled: true
  }
  editDialogVisible.value = true
}

/**
 * 显示编辑模型对话框
 */
function showEditDialog(row: ModelData) {
  editDialogTitle.value = "编辑模型"
  isEditing.value = true
  editForm.value = { 
    ...row,
    api_key: ""
  }
  editDialogVisible.value = true
}

/**
 * 提交新增/编辑表单
 */
async function handleSubmitEdit() {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    
    if (isEditing.value) {
      const response = await axios.post("/api/v1/dialog/model/update", editForm.value)
      if (response.data.code === 0) {
        ElMessage.success("模型更新成功")
        editDialogVisible.value = false
        getModelList()
      } else {
        ElMessage.error(response.data.message || "更新失败")
      }
    } else {
      const response = await axios.post("/api/v1/dialog/model/create", editForm.value)
      if (response.data.code === 0) {
        ElMessage.success("模型添加成功")
        editDialogVisible.value = false
        getModelList()
      } else {
        ElMessage.error(response.data.message || "添加失败")
      }
    }
  } catch (validationError) {
    console.log("表单验证失败")
  }
}

/**
 * 删除模型
 */
function handleDelete(row: ModelData) {
  ElMessageBox.confirm(
    `确定要删除模型 "${row.llm_name}" 吗？此操作不可恢复。`,
    "删除确认",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    }
  ).then(async () => {
    try {
      const response = await axios.post("/api/v1/dialog/model/delete", {
        llm_name: row.llm_name,
        llm_factory: row.llm_factory
      })
      if (response.data.code === 0) {
        ElMessage.success("模型删除成功")
        getModelList()
      } else {
        ElMessage.error(response.data.message || "删除失败")
      }
    } catch (error) {
      console.error("删除模型失败:", error)
      ElMessage.error("删除失败")
    }
  }).catch(() => {})
}

/**
 * 批量删除
 */
function handleBatchDelete() {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning("请至少选择一条记录")
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${multipleSelection.value.length} 个模型吗？此操作不可恢复。`,
    "批量删除确认",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    }
  ).then(async () => {
    loading.value = true
    try {
      // 并行删除所有选中的模型
      await Promise.all(
        multipleSelection.value.map(row => 
          axios.post("/api/v1/dialog/model/delete", {
            llm_name: row.llm_name,
            llm_factory: row.llm_factory
          })
        )
      )
      ElMessage.success("批量删除成功")
      getModelList()
    } catch (error) {
      console.error("批量删除失败:", error)
      ElMessage.error("批量删除失败")
    } finally {
      loading.value = false
    }
  }).catch(() => {})
}

// 角色权限设置
const roleDialogVisible = ref(false)
const roleLoading = ref(false)
const currentModelForRole = ref<ModelData | null>(null)
const allRoles = ref<RoleData[]>([])
const selectedRoleIds = ref<string[]>([])

async function handleSetModelRoles(row: ModelData) {
  currentModelForRole.value = row
  roleDialogVisible.value = true
  roleLoading.value = true
  
  try {
    const [allRolesRes, modelRolesRes] = await Promise.all([
      getAllRolesApi(),
      axios.get(`/api/v1/dialog/model/${encodeURIComponent(row.llm_factory)}/${encodeURIComponent(row.llm_name)}/roles`)
    ])
    allRoles.value = allRolesRes.data || []
    selectedRoleIds.value = (modelRolesRes.data.data || []).map((r: any) => r.id)
  } catch (error: any) {
    console.error("获取角色信息失败:", error)
    ElMessage.error("获取角色信息失败")
  } finally {
    roleLoading.value = false
  }
}

async function submitModelRoles() {
  if (!currentModelForRole.value) return
  
  roleLoading.value = true
  try {
    await axios.put(
      `/api/v1/dialog/model/${encodeURIComponent(currentModelForRole.value.llm_factory)}/${encodeURIComponent(currentModelForRole.value.llm_name)}/roles`,
      { role_ids: selectedRoleIds.value }
    )
    ElMessage.success("角色权限设置成功")
    roleDialogVisible.value = false
  } catch (error: any) {
    console.error("设置角色权限失败:", error)
    ElMessage.error("设置角色权限失败")
  } finally {
    roleLoading.value = false
  }
}

function roleDialogClosed() {
  currentModelForRole.value = null
  selectedRoleIds.value = []
}

onMounted(async () => {
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
        <el-col :span="12">
          <el-button type="primary" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleRefresh">
            重置
          </el-button>
          <el-button type="success" :icon="Plus" @click="showAddDialog">
            新增模型
          </el-button>
          <el-button type="danger" :icon="Delete" @click="handleBatchDelete">
            批量删除
          </el-button>
        </el-col>
        <el-col :span="6" style="text-align: right">
          <el-text type="info">
            启用的模型将对所有前台用户可见
          </el-text>
        </el-col>
      </el-row>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="hover" class="table-wrapper">
      <el-table 
        ref="tableRef"
        v-loading="loading" 
        :data="modelList" 
        border 
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column label="启用" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.global_enabled"
              @change="handleToggleEnabled(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="llm_name" label="模型名称" min-width="200" />
        <el-table-column prop="llm_factory" label="模型厂商" min-width="150" />
        <el-table-column prop="model_type" label="模型类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.model_type === 'chat' ? 'success' : 'info'">
              {{ row.model_type === 'chat' ? '对话' : row.model_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="api_base" label="API Base" min-width="200">
          <template #default="{ row }">
            {{ row.api_base || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div style="display: flex; gap: 8px; justify-content: center;">
              <el-button type="primary" link size="small" :icon="Edit" @click="showEditDialog(row)">
                编辑
              </el-button>
              <el-button type="success" link size="small" @click="handleSetModelRoles(row)">
                角色
              </el-button>
              <el-button type="danger" link size="small" :icon="Delete" @click="handleDelete(row)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="total > 0"
        class="pagination"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :current-page="currentPage"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      :title="editDialogTitle"
      width="550px"
      destroy-on-close
    >
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="100px">
        <el-form-item label="模型名称" prop="llm_name">
          <el-input 
            v-model="editForm.llm_name" 
            placeholder="例如: qwen-max, gpt-4o"
            :disabled="isEditing"
          />
        </el-form-item>
        <el-form-item label="模型厂商" prop="llm_factory">
          <el-select v-model="editForm.llm_factory" placeholder="请选择" :disabled="isEditing" style="width: 100%">
            <el-option label="OpenAI-API-Compatible" value="OpenAI-API-Compatible" />
            <el-option label="Tongyi-Qianwen" value="Tongyi-Qianwen" />
            <el-option label="Zhipu-AI" value="Zhipu-AI" />
            <el-option label="DeepSeek" value="DeepSeek" />
            <el-option label="Moonshot" value="Moonshot" />
            <el-option label="VolcEngine" value="VolcEngine" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Base" prop="api_base">
          <el-input v-model="editForm.api_base" placeholder="例如: https://api.openai.com/v1" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input 
            v-model="editForm.api_key" 
            type="password" 
            show-password 
            :placeholder="isEditing ? '留空则不修改' : '请输入 API Key'"
          />
        </el-form-item>
        <el-form-item label="全局启用">
          <el-switch v-model="editForm.global_enabled" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            启用后前台用户可选择此模型
          </span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" @click="handleSubmitEdit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 设置模型角色权限对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      :title="`设置角色权限 - ${currentModelForRole?.llm_name || ''}`"
      width="500px"
      @closed="roleDialogClosed"
    >
      <div v-loading="roleLoading">
        <p style="margin-bottom: 15px; color: #909399; font-size: 13px;">
          选择可以使用此模型的角色。如果不选择任何角色，则所有角色都可以使用。
        </p>
        <el-checkbox-group v-model="selectedRoleIds">
          <el-checkbox
            v-for="role in allRoles"
            :key="role.id"
            :value="role.id"
            :label="role.id"
            style="display: block; margin-bottom: 10px;"
          >
            {{ role.name }}
            <el-tag v-if="role.isDefault" type="success" size="small" style="margin-left: 8px;">默认</el-tag>
          </el-checkbox>
        </el-checkbox-group>
        <el-empty v-if="allRoles.length === 0 && !roleLoading" description="暂无可用角色，请先创建角色" />
      </div>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="roleLoading" @click="submitModelRoles">确认</el-button>
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
</style>

