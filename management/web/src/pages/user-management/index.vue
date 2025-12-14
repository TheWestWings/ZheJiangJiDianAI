<script lang="ts" setup>
import type { CreateOrUpdateTableRequestData, TableData } from "@@/apis/tables/type"
import type { FormInstance, FormRules } from "element-plus"
import { createTableDataApi, deleteTableDataApi, getTableDataApi, resetPasswordApi, updateTableDataApi } from "@@/apis/tables"
import { getAllRolesApi, getUserRolesApi, setUserRolesApi, type RoleData } from "@@/apis/roles"
import { usePagination } from "@@/composables/usePagination"
import { CirclePlus, Delete, Edit, Key, Refresh, RefreshRight, Search, UserFilled, Upload, Download, Avatar, ArrowDown } from "@element-plus/icons-vue"
import { cloneDeep } from "lodash-es"
import { request } from "@/http/axios"
import { useUserStore } from "@/pinia/stores/user"

const userStore = useUserStore()

defineOptions({
  // 命名当前组件
  name: "UserManagement"
})

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// #region 增
const DEFAULT_FORM_DATA: CreateOrUpdateTableRequestData = {
  id: undefined,
  username: "",
  email: "",
  password: "",
  gender: "",
  department: "",
  phone: ""
}
const dialogVisible = ref<boolean>(false)
const formRef = ref<FormInstance | null>(null)
const formData = ref<CreateOrUpdateTableRequestData>(cloneDeep(DEFAULT_FORM_DATA))
const formRules: FormRules<CreateOrUpdateTableRequestData> = {
  username: [{ required: true, trigger: "blur", message: "请输入姓名" }],
  email: [
    { required: true, trigger: "blur", message: "请输入学号/工号" }
  ],
  password: [{ required: true, trigger: "blur", message: "请输入密码" }]
}
// #region 重置密码
const resetPasswordDialogVisible = ref<boolean>(false)
const resetPasswordFormRef = ref<FormInstance | null>(null)
const currentUserId = ref<string | undefined>(undefined) // 用于存储当前要重置密码的用户ID
const resetPasswordFormData = reactive({
  password: ""
})
const resetPasswordFormRules: FormRules = {
  password: [
    { required: true, message: "请输入新密码", trigger: "blur" }
  ]
}
// #endregion

// #region 设置角色
const roleDialogVisible = ref<boolean>(false)
const roleLoading = ref<boolean>(false)
const currentRoleUserId = ref<string | undefined>(undefined)
const allRoles = ref<RoleData[]>([])
const selectedRoleIds = ref<string[]>([])

function handleSetRoles(row: TableData) {
  currentRoleUserId.value = row.id
  roleDialogVisible.value = true
  roleLoading.value = true
  
  // 并行获取所有角色和用户当前角色
  Promise.all([
    getAllRolesApi(),
    getUserRolesApi(row.id)
  ]).then(([allRolesRes, userRolesRes]) => {
    allRoles.value = allRolesRes.data || []
    selectedRoleIds.value = (userRolesRes.data || []).map((r: RoleData) => r.id!)
  }).catch((error: any) => {
    console.error("获取角色信息失败:", error)
    ElMessage.error("获取角色信息失败")
  }).finally(() => {
    roleLoading.value = false
  })
}

function submitSetRoles() {
  if (currentRoleUserId.value === undefined) {
    ElMessage.error("用户ID丢失")
    return
  }
  roleLoading.value = true
  setUserRolesApi(currentRoleUserId.value, selectedRoleIds.value)
    .then(() => {
      ElMessage.success("角色设置成功")
      roleDialogVisible.value = false
    })
    .catch((error: any) => {
      console.error("设置角色失败:", error)
      ElMessage.error("设置角色失败")
    })
    .finally(() => {
      roleLoading.value = false
    })
}

function roleDialogClosed() {
  currentRoleUserId.value = undefined
  selectedRoleIds.value = []
}
// #endregion

// #region 系统管理员设置
async function handleSetSystemAdmin(row: TableData) {
  const isCurrentlyAdmin = row.is_system_admin
  const action = isCurrentlyAdmin ? '取消' : '设置'
  
  try {
    await ElMessageBox.confirm(
      `确认${action}用户 "${row.username}" 为系统管理员？`,
      '提示',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    
    const endpoint = isCurrentlyAdmin 
      ? `/api/v1/users/${row.id}/unset-system-admin`
      : `/api/v1/users/${row.id}/set-system-admin`
    
    const response = await request<{ code: number; message: string }>({
      url: endpoint,
      method: 'POST'
    })
    if (response.code === 0) {
      ElMessage.success(`${action}系统管理员成功`)
      getTableData()
    } else {
      ElMessage.error(response.message || `${action}系统管理员失败`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error(`${action}系统管理员失败:`, error)
      ElMessage.error(error.message || `${action}系统管理员失败`)
    }
  }
}
// #endregion

// #region 下拉菜单命令处理
function handleDropdownCommand(command: string, row: TableData) {
  switch (command) {
    case 'setRoles':
      handleSetRoles(row)
      break
    case 'resetPassword':
      handleResetPassword(row)
      break
    case 'toggleAdmin':
      handleSetSystemAdmin(row)
      break
    case 'delete':
      handleDelete(row)
      break
  }
}
// #endregion

// #region 批量导入
const batchImportDialogVisible = ref<boolean>(false)
const batchImportLoading = ref<boolean>(false)
const uploadRef = ref<any>(null)
const batchImportResult = ref<{
  success_count: number
  failed_count: number
  failed_users: { row: number; email: string; reason: string }[]
} | null>(null)

function handleBatchImport() {
  batchImportDialogVisible.value = true
  batchImportResult.value = null
}

function downloadTemplate() {
  const link = document.createElement('a')
  link.href = '/api/v1/users/template'
  link.download = 'user_import_template.xlsx'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function handleUploadSuccess(response: any, file: any, fileList: any) {
  batchImportLoading.value = false
  if (response.code === 0) {
    batchImportResult.value = response.data
    ElMessage.success(response.message)
    getTableData()
  } else {
    ElMessage.error(response.message || '批量导入失败')
  }
  // 清空上传文件列表
  uploadRef.value?.clearFiles()
}

function handleUploadError(error: any) {
  batchImportLoading.value = false
  ElMessage.error('文件上传失败')
  console.error('Upload error:', error)
}

function beforeUpload(file: File) {
  const isExcel = file.name.endsWith('.xlsx') || file.name.endsWith('.xls')
  if (!isExcel) {
    ElMessage.error('请上传 Excel 文件（.xlsx 或 .xls）')
    return false
  }
  batchImportLoading.value = true
  batchImportResult.value = null
  return true
}

function batchImportDialogClosed() {
  batchImportResult.value = null
  uploadRef.value?.clearFiles()
}
// #endregion
function handleCreateOrUpdate() {
  formRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("登录校验不通过")
      return
    }
    loading.value = true
    const api = formData.value.id === undefined ? createTableDataApi : updateTableDataApi
    api(formData.value).then(() => {
      ElMessage.success("操作成功")
      dialogVisible.value = false
      getTableData()
    }).finally(() => {
      loading.value = false
    })
  })
}
function resetForm() {
  formRef.value?.clearValidate()
  formData.value = cloneDeep(DEFAULT_FORM_DATA)
}
// #endregion

// #region 重置密码处理
/**
 * 打开重置密码对话框
 * @param {TableData} row - 当前行用户数据
 */
function handleResetPassword(row: TableData) {
  currentUserId.value = row.id
  resetPasswordFormData.password = "" // 清空上次输入
  resetPasswordDialogVisible.value = true
  // 清除之前的校验状态
  nextTick(() => {
    resetPasswordFormRef.value?.clearValidate()
  })
}

/**
 * 提交重置密码表单
 */
function submitResetPassword() {
  resetPasswordFormRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    if (currentUserId.value === undefined) {
      ElMessage.error("用户ID丢失，无法重置密码")
      return
    }
    loading.value = true
    // 调用后端API重置密码
    resetPasswordApi(currentUserId.value, resetPasswordFormData.password)
      .then(() => {
        ElMessage.success("密码重置成功")
        resetPasswordDialogVisible.value = false
      })
      .catch((error: any) => {
        console.error("重置密码失败:", error)
        ElMessage.error("密码重置失败")
      })
      .finally(() => {
        loading.value = false
      })
  })
}

/**
 * 关闭重置密码对话框时重置状态
 */
function resetPasswordDialogClosed() {
  currentUserId.value = undefined
  resetPasswordFormRef.value?.resetFields() // 重置表单字段
}
// #endregion

// #region 删
function handleDelete(row: TableData) {
  ElMessageBox.confirm(`正在删除用户：${row.username}，确认删除？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteTableDataApi(row.id).then(() => {
      ElMessage.success("删除成功")
      getTableData()
    })
  })
}
// #endregion

// #region 改
function handleUpdate(row: TableData) {
  dialogVisible.value = true
  formData.value = cloneDeep(row)
}
// #endregion

// #region 查
const tableData = ref<TableData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  username: "",
  email: ""
})

// 排序状态
const sortData = reactive({
  sortBy: "create_date",
  sortOrder: "desc" // 默认排序顺序 (最新创建的在前)
})

// 存储多选的表格数据
const multipleSelection = ref<TableData[]>([])

function getTableData() {
  loading.value = true
  getTableDataApi({
    currentPage: paginationData.currentPage,
    size: paginationData.pageSize,
    username: searchData.username,
    email: searchData.email,
    sort_by: sortData.sortBy,
    sort_order: sortData.sortOrder
  }).then(({ data }) => {
    paginationData.total = data.total
    tableData.value = data.list
    // 清空选中数据
    multipleSelection.value = []
  }).catch(() => {
    tableData.value = []
  }).finally(() => {
    loading.value = false
  })
}
function handleSearch() {
  paginationData.currentPage === 1 ? getTableData() : (paginationData.currentPage = 1)
}
function resetSearch() {
  searchFormRef.value?.resetFields()
  handleSearch()
}

// 表格多选事件处理
function handleSelectionChange(selection: TableData[]) {
  multipleSelection.value = selection
}

// 批量删除方法
function handleBatchDelete() {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning("请至少选择一条记录")
    return
  }
  ElMessageBox.confirm(`确认删除选中的 ${multipleSelection.value.length} 条记录吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(async () => {
    loading.value = true
    try {
      // 使用 Promise.all 并行处理所有删除请求
      await Promise.all(
        multipleSelection.value.map(row => deleteTableDataApi(row.id))
      )
      ElMessage.success("批量删除成功")
      getTableData()
    } catch {
      ElMessage.error("批量删除失败")
    } finally {
      loading.value = false
    }
  })
}
// #endregion

/**
 * @description 处理表格排序变化事件（只允许正序和倒序切换）
 * @param {object} sortInfo 排序信息对象，包含 prop 和 order
 * @param {string} sortInfo.prop 排序的字段名
 * @param {string | null} sortInfo.order 排序的顺序 ('ascending', 'descending', null)
 */
function handleSortChange({ prop }: { prop: string, order: string | null }) {
  // 如果点击的是同一个字段，则切换排序顺序
  if (sortData.sortBy === prop) {
    // 当前为正序则切换为倒序，否则切换为正序
    sortData.sortOrder = sortData.sortOrder === "asc" ? "desc" : "asc"
  } else {
    // 切换字段时，默认正序
    sortData.sortBy = prop
    sortData.sortOrder = "asc"
  }
  getTableData()
}

// 监听分页参数的变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getTableData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="username" label="用户名">
          <el-input v-model="searchData.username" placeholder="请输入" />
        </el-form-item>
        <el-form-item prop="email" label="邮箱">
          <el-input v-model="searchData.email" placeholder="请输入" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            查询
          </el-button>
          <el-button :icon="Refresh" @click="resetSearch">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card v-loading="loading" shadow="never">
      <div class="toolbar-wrapper">
        <div>
          <el-button type="primary" :icon="CirclePlus" @click="dialogVisible = true">
            新增用户
          </el-button>
          <el-button type="success" :icon="Upload" @click="handleBatchImport">
            批量新增
          </el-button>
          <el-button type="danger" :icon="Delete" @click="handleBatchDelete">
            批量删除
          </el-button>
        </div>
        <div>
          <el-tooltip content="刷新当前页">
            <el-button type="primary" :icon="RefreshRight" circle @click="getTableData" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table :data="tableData" @selection-change="handleSelectionChange" @sort-change="handleSortChange">
          <el-table-column type="selection" width="50" align="center" />
          <el-table-column prop="email" label="学号/工号" align="center" sortable="custom" />
          <el-table-column prop="username" label="姓名" align="center" sortable="custom" />
          <el-table-column label="管理员角色" width="150" align="center">
            <template #default="scope">
              <el-tag v-if="scope.row.is_super_admin" type="danger" size="small">超级管理员</el-tag>
              <el-tag v-else-if="scope.row.is_system_admin" type="warning" size="small">系统管理员</el-tag>
              <span v-else style="color: #999;">-</span>
            </template>
          </el-table-column>
          <el-table-column prop="gender" label="性别" width="80" align="center" />
          <el-table-column prop="department" label="部门" align="center" />
          <el-table-column prop="phone" label="电话" align="center" />
          <el-table-column prop="createTime" label="创建时间" align="center" sortable="custom" />
          <el-table-column fixed="right" label="操作" width="220" align="center">
            <template #default="scope">
              <el-button type="primary" text bg size="small" :icon="Edit" @click="handleUpdate(scope.row)">
                编辑
              </el-button>
              <el-dropdown trigger="click" @command="(cmd: string) => handleDropdownCommand(cmd, scope.row)">
                <el-button type="info" text bg size="small">
                  更多
                  <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="setRoles" :icon="UserFilled">
                      设置角色
                    </el-dropdown-item>
                    <el-dropdown-item command="resetPassword" :icon="Key">
                      重置密码
                    </el-dropdown-item>
                    <el-dropdown-item 
                      v-if="!scope.row.is_super_admin && userStore.is_super_admin"
                      command="toggleAdmin"
                      :icon="Avatar"
                    >
                      {{ scope.row.is_system_admin ? '取消系统管理员' : '设置系统管理员' }}
                    </el-dropdown-item>
                    <el-dropdown-item divided command="delete" :icon="Delete" style="color: var(--el-color-danger);">
                      删除用户
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="pager-wrapper">
        <el-pagination
          background
          :layout="paginationData.layout"
          :page-sizes="paginationData.pageSizes"
          :total="paginationData.total"
          :page-size="paginationData.pageSize"
          :current-page="paginationData.currentPage"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    <!-- 新增/修改 -->
    <el-dialog
      v-model="dialogVisible"
      :title="formData.id === undefined ? '新增用户' : '修改用户'"
      width="30%"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="email" label="学号/工号">
          <el-input v-model="formData.email" placeholder="请输入学号/工号" :disabled="formData.id !== undefined" />
        </el-form-item>
        <el-form-item prop="username" label="姓名">
          <el-input v-model="formData.username" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item v-if="formData.id === undefined" prop="password" label="密码">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item prop="gender" label="性别">
          <el-select v-model="formData.gender" placeholder="请选择" clearable style="width: 100%">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
          </el-select>
        </el-form-item>
        <el-form-item prop="department" label="部门">
          <el-input v-model="formData.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item prop="phone" label="电话">
          <el-input v-model="formData.phone" placeholder="请输入电话" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="loading" @click="handleCreateOrUpdate">
          确认
        </el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPasswordDialogVisible"
      title="重置密码"
      width="30%"
      @closed="resetPasswordDialogClosed"
    >
      <el-form ref="resetPasswordFormRef" :model="resetPasswordFormData" :rules="resetPasswordFormRules" label-width="100px" label-position="left">
        <el-form-item prop="password" label="新密码">
          <el-input v-model="resetPasswordFormData.password" type="password" show-password placeholder="请输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="loading" @click="submitResetPassword">
          确认重置
        </el-button>
      </template>
    </el-dialog>

    <!-- 设置角色对话框 -->
    <el-dialog
      v-model="roleDialogVisible"
      title="设置用户角色"
      width="500px"
      @closed="roleDialogClosed"
    >
      <div v-loading="roleLoading">
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
        <el-empty v-if="allRoles.length === 0 && !roleLoading" description="暂无可用角色" />
      </div>
      <template #footer>
        <el-button @click="roleDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="roleLoading" @click="submitSetRoles">
          确认
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog
      v-model="batchImportDialogVisible"
      title="批量新增用户"
      width="500px"
      @closed="batchImportDialogClosed"
    >
      <div v-loading="batchImportLoading">
        <el-alert
          title="请按照模板格式填写用户信息，包含 username、email、password 三列"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        />
        
        <div style="margin-bottom: 20px;">
          <el-button type="primary" :icon="Download" @click="downloadTemplate">
            下载模板
          </el-button>
        </div>
        
        <el-upload
          ref="uploadRef"
          action="/api/v1/users/batch"
          :limit="1"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          :before-upload="beforeUpload"
          accept=".xlsx,.xls"
          drag
        >
          <el-icon class="el-icon--upload"><Upload /></el-icon>
          <div class="el-upload__text">
            将 Excel 文件拖到此处，或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              仅支持 .xlsx 和 .xls 格式的 Excel 文件
            </div>
          </template>
        </el-upload>
        
        <!-- 导入结果 -->
        <div v-if="batchImportResult" style="margin-top: 20px;">
          <el-alert
            :title="`成功创建 ${batchImportResult.success_count} 个用户`"
            :type="batchImportResult.failed_count > 0 ? 'warning' : 'success'"
            :closable="false"
          />
          <div v-if="batchImportResult.failed_count > 0" style="margin-top: 10px;">
            <el-text type="danger">以下用户创建失败：</el-text>
            <el-table :data="batchImportResult.failed_users" size="small" style="margin-top: 8px;">
              <el-table-column prop="row" label="行号" width="60" />
              <el-table-column prop="email" label="邮箱" />
              <el-table-column prop="reason" label="原因" />
            </el-table>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="batchImportDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.el-alert {
  margin-bottom: 20px;
}

.search-wrapper {
  margin-bottom: 20px;
  :deep(.el-card__body) {
    padding-bottom: 2px;
  }
}

.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.table-wrapper {
  margin-bottom: 20px;
}

.pager-wrapper {
  display: flex;
  justify-content: flex-end;
}
</style>
