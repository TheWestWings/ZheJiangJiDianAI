<script lang="ts" setup>
import type { FormInstance, FormRules } from "element-plus"
import {
  getRolesApi,
  createRoleApi,
  updateRoleApi,
  deleteRoleApi,
  setDefaultRoleApi,
  unsetDefaultRoleApi,
  getRoleUsersApi,
  type RoleData,
  type RoleUser
} from "@@/apis/roles"
import { usePagination } from "@@/composables/usePagination"
import { CirclePlus, Delete, Edit, Refresh, RefreshRight, Search, User } from "@element-plus/icons-vue"
import { cloneDeep } from "lodash-es"

defineOptions({
  name: "RoleManagement"
})

const loading = ref<boolean>(false)
const { paginationData, handleCurrentChange, handleSizeChange } = usePagination()

// #region 角色列表
const tableData = ref<RoleData[]>([])
const searchFormRef = ref<FormInstance | null>(null)
const searchData = reactive({
  name: ""
})

const sortData = reactive({
  sortBy: "create_date",
  sortOrder: "desc"
})

function getTableData() {
  loading.value = true
  getRolesApi({
    currentPage: paginationData.currentPage,
    size: paginationData.pageSize,
    name: searchData.name,
    sort_by: sortData.sortBy,
    sort_order: sortData.sortOrder
  }).then(({ data }) => {
    paginationData.total = data.total
    tableData.value = data.list
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

function handleSortChange({ prop }: { prop: string, order: string | null }) {
  if (sortData.sortBy === prop) {
    sortData.sortOrder = sortData.sortOrder === "asc" ? "desc" : "asc"
  } else {
    sortData.sortBy = prop
    sortData.sortOrder = "asc"
  }
  getTableData()
}
// #endregion

// #region 新增/编辑角色
const DEFAULT_FORM_DATA: RoleData = {
  id: undefined,
  name: "",
  description: "",
  status: "1"
}
const dialogVisible = ref<boolean>(false)
const formRef = ref<FormInstance | null>(null)
const formData = ref<RoleData>(cloneDeep(DEFAULT_FORM_DATA))
const formRules: FormRules<RoleData> = {
  name: [
    { required: true, trigger: "blur", message: "请输入角色名称" },
    { min: 2, max: 64, message: "长度在 2 到 64 个字符", trigger: "blur" }
  ]
}

function handleCreateOrUpdate() {
  formRef.value?.validate((valid) => {
    if (!valid) {
      ElMessage.error("表单校验不通过")
      return
    }
    loading.value = true
    const api = formData.value.id === undefined ? createRoleApi : updateRoleApi
    const params = formData.value.id === undefined
      ? { name: formData.value.name, description: formData.value.description }
      : formData.value
    const apiCall = formData.value.id === undefined
      ? api(params as any)
      : (api as typeof updateRoleApi)(formData.value.id!, params)

    apiCall.then(() => {
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

function handleUpdate(row: RoleData) {
  dialogVisible.value = true
  formData.value = cloneDeep(row)
}
// #endregion

// #region 删除角色
function handleDelete(row: RoleData) {
  ElMessageBox.confirm(`确定要删除角色 "${row.name}" 吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(() => {
    deleteRoleApi(row.id!).then(() => {
      ElMessage.success("删除成功")
      getTableData()
    }).catch((error: any) => {
      ElMessage.error(error?.response?.data?.message || "删除失败")
    })
  })
}
// #endregion

// #region 默认角色
function handleToggleDefault(row: RoleData) {
  const api = row.isDefault ? unsetDefaultRoleApi : setDefaultRoleApi
  api(row.id!).then(() => {
    ElMessage.success(row.isDefault ? "已取消默认角色" : "已设置为默认角色")
    getTableData()
  }).catch(() => {
    ElMessage.error("操作失败")
  })
}
// #endregion

// #region 查看角色用户
const usersDialogVisible = ref<boolean>(false)
const usersLoading = ref<boolean>(false)
const currentRole = ref<RoleData | null>(null)
const userList = ref<RoleUser[]>([])
const usersPaginationData = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

function handleViewUsers(row: RoleData) {
  currentRole.value = row
  usersDialogVisible.value = true
  usersPaginationData.currentPage = 1
  getUserList()
}

function getUserList() {
  if (!currentRole.value) return
  usersLoading.value = true
  getRoleUsersApi(currentRole.value.id!, {
    currentPage: usersPaginationData.currentPage,
    size: usersPaginationData.pageSize
  }).then(({ data }) => {
    userList.value = data.list
    usersPaginationData.total = data.total
  }).catch(() => {
    userList.value = []
  }).finally(() => {
    usersLoading.value = false
  })
}

function handleUsersPageChange(page: number) {
  usersPaginationData.currentPage = page
  getUserList()
}
// #endregion

// 监听分页参数变化
watch([() => paginationData.currentPage, () => paginationData.pageSize], getTableData, { immediate: true })
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never" class="search-wrapper">
      <el-form ref="searchFormRef" :inline="true" :model="searchData">
        <el-form-item prop="name" label="角色名称">
          <el-input v-model="searchData.name" placeholder="请输入" />
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
            新增角色
          </el-button>
        </div>
        <div>
          <el-tooltip content="刷新当前页">
            <el-button type="primary" :icon="RefreshRight" circle @click="getTableData" />
          </el-tooltip>
        </div>
      </div>
      <div class="table-wrapper">
        <el-table :data="tableData" @sort-change="handleSortChange">
          <el-table-column prop="name" label="角色名称" align="center" sortable="custom" />
          <el-table-column prop="description" label="描述" align="center" show-overflow-tooltip />
          <el-table-column label="默认角色" width="100" align="center">
            <template #default="scope">
              <el-switch
                :model-value="scope.row.isDefault"
                @change="handleToggleDefault(scope.row)"
                :active-text="scope.row.isDefault ? '是' : ''"
              />
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="scope">
              <el-tag :type="scope.row.status === '1' ? 'success' : 'danger'">
                {{ scope.row.status === '1' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="创建时间" align="center" sortable="custom" />
          <el-table-column fixed="right" label="操作" width="250" align="center">
            <template #default="scope">
              <el-button type="primary" text bg size="small" :icon="User" @click="handleViewUsers(scope.row)">
                查看用户
              </el-button>
              <el-button type="primary" text bg size="small" :icon="Edit" @click="handleUpdate(scope.row)">
                编辑
              </el-button>
              <el-button type="danger" text bg size="small" :icon="Delete" @click="handleDelete(scope.row)">
                删除
              </el-button>
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="formData.id === undefined ? '新增角色' : '编辑角色'"
      width="500px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="100px" label-position="left">
        <el-form-item prop="name" label="角色名称">
          <el-input v-model="formData.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item prop="description" label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item v-if="formData.id !== undefined" prop="status" label="状态">
          <el-radio-group v-model="formData.status">
            <el-radio value="1">启用</el-radio>
            <el-radio value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleCreateOrUpdate">确认</el-button>
      </template>
    </el-dialog>

    <!-- 角色用户对话框 -->
    <el-dialog
      v-model="usersDialogVisible"
      :title="`角色用户 - ${currentRole?.name || ''}`"
      width="600px"
    >
      <el-table v-loading="usersLoading" :data="userList" max-height="400">
        <el-table-column prop="username" label="用户名" align="center" />
        <el-table-column prop="email" label="邮箱" align="center" />
        <el-table-column prop="createTime" label="加入时间" align="center" />
      </el-table>
      <div v-if="usersPaginationData.total > usersPaginationData.pageSize" class="pager-wrapper" style="margin-top: 20px;">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="usersPaginationData.total"
          :page-size="usersPaginationData.pageSize"
          :current-page="usersPaginationData.currentPage"
          @current-change="handleUsersPageChange"
        />
      </div>
      <template #footer>
        <el-button @click="usersDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
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
