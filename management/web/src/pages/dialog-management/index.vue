<script lang="ts" setup>
import { Refresh, Plus, Edit, Delete, Star, StarFilled, QuestionFilled } from "@element-plus/icons-vue"
import axios from "axios"

defineOptions({
  name: "DialogManagement"
})

// 助理数据类型
interface DialogData {
  id: string
  name: string
  description: string
  tenant_id: string
  tenant_name?: string
  llm_id: string
  kb_ids: string[]
  kb_names?: string[]
  prompt_config: {
    system: string
    prologue: string
    empty_response: string
    parameters: { key: string; optional: boolean }[]
  }
  llm_setting: {
    temperature: number
    top_p: number
    max_tokens: number
  }
  top_n: number
  top_k: number
  similarity_threshold: number
  vector_similarity_weight: number
  rerank_id: string
  icon: string
  create_time: number
  update_time: number
  is_default?: boolean
}

interface TenantData {
  id: string
  name: string
}

interface KnowledgebaseData {
  id: string
  name: string
  embd_id: string
}

interface LlmData {
  llm_name: string
  llm_factory: string
  model_type: string
}

// 状态
const loading = ref(false)
const dialogList = ref<DialogData[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchName = ref("")
const defaultDialogId = ref<string | null>(null)

// 选项数据
const tenantList = ref<TenantData[]>([])
const knowledgebaseList = ref<KnowledgebaseData[]>([])
const llmList = ref<LlmData[]>([])

// 编辑对话框状态
const editDialogVisible = ref(false)
const editDialogTitle = ref("新增助理")
const isEditing = ref(false)
const editForm = ref<Partial<DialogData>>({
  name: "",
  description: "",
  tenant_id: "",
  llm_id: "",
  kb_ids: [],
  prompt_config: {
    system: `你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括"知识库中未找到您要的答案！"这句话。回答需要考虑聊天历史。
以下是知识库：
{knowledge}
以上是知识库。`,
    prologue: "您好，我是您的智能助手，有什么可以帮您？",
    empty_response: "抱歉，知识库中未找到相关内容！",
    parameters: [{ key: "knowledge", optional: false }]
  },
  llm_setting: {
    temperature: 0.1,
    top_p: 0.3,
    max_tokens: 512
  },
  top_n: 6,
  top_k: 1024,
  similarity_threshold: 0.1,
  vector_similarity_weight: 0.3,
  rerank_id: ""
})

const editFormRef = ref()

// 表单规则
const editFormRules = {
  name: [{ required: true, message: "请输入助理名称", trigger: "blur" }]
}

/**
 * 获取助理列表
 */
async function getDialogList() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      size: pageSize.value
    }
    if (searchName.value) {
      params.name = searchName.value
    }
    const response = await axios.get("/api/v1/dialog", { params })
    if (response.data.code === 0) {
      dialogList.value = response.data.data.list || []
      total.value = response.data.data.total || 0
      
      // 标记默认助理
      dialogList.value.forEach(d => {
        d.is_default = d.id === defaultDialogId.value
      })
    }
  } catch (error) {
    console.error("获取助理列表失败:", error)
    ElMessage.error("获取助理列表失败")
  } finally {
    loading.value = false
  }
}

/**
 * 获取默认助理ID
 */
async function getDefaultDialog() {
  try {
    const response = await axios.get("/api/v1/dialog/default")
    if (response.data.code === 0) {
      defaultDialogId.value = response.data.data?.dialog_id || null
    }
  } catch (error) {
    console.error("获取默认助理失败:", error)
  }
}

/**
 * 获取租户列表
 */
async function getTenantList() {
  try {
    const response = await axios.get("/api/v1/dialog/tenants")
    if (response.data.code === 0) {
      tenantList.value = response.data.data || []
    }
  } catch (error) {
    console.error("获取租户列表失败:", error)
  }
}

/**
 * 获取知识库列表
 */
async function getKnowledgebaseList() {
  try {
    const response = await axios.get("/api/v1/dialog/knowledgebases")
    if (response.data.code === 0) {
      knowledgebaseList.value = response.data.data || []
    }
  } catch (error) {
    console.error("获取知识库列表失败:", error)
  }
}

/**
 * 获取LLM列表
 */
async function getLlmList() {
  try {
    const response = await axios.get("/api/v1/dialog/llms")
    if (response.data.code === 0) {
      llmList.value = response.data.data || []
    }
  } catch (error) {
    console.error("获取LLM列表失败:", error)
  }
}

/**
 * 设置默认助理
 */
async function setDefaultDialog(dialogId: string) {
  try {
    const response = await axios.post(`/api/v1/dialog/${dialogId}/set-default`)
    if (response.data.code === 0) {
      defaultDialogId.value = dialogId
      ElMessage.success("设置默认助理成功")
      // 更新列表中的默认标记
      dialogList.value.forEach(d => {
        d.is_default = d.id === dialogId
      })
    } else {
      ElMessage.error(response.data.message || "设置默认助理失败")
    }
  } catch (error) {
    console.error("设置默认助理失败:", error)
    ElMessage.error("设置默认助理失败")
  }
}

/**
 * 打开新增对话框
 */
function handleAdd() {
  isEditing.value = false
  editDialogTitle.value = "新增助理"
  editForm.value = {
    name: "",
    description: "",
    tenant_id: "",
    llm_id: "",
    kb_ids: [],
    prompt_config: {
      system: `你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括"知识库中未找到您要的答案！"这句话。回答需要考虑聊天历史。
以下是知识库：
{knowledge}
以上是知识库。`,
      prologue: "您好，我是您的智能助手，有什么可以帮您？",
      empty_response: "抱歉，知识库中未找到相关内容！",
      parameters: [{ key: "knowledge", optional: false }]
    },
    llm_setting: {
      temperature: 0.1,
      top_p: 0.3,
      max_tokens: 512
    },
    top_n: 6,
    top_k: 1024,
    similarity_threshold: 0.1,
    vector_similarity_weight: 0.3,
    rerank_id: ""
  }
  editDialogVisible.value = true
}

/**
 * 打开编辑对话框
 */
async function handleEdit(row: DialogData) {
  isEditing.value = true
  editDialogTitle.value = "编辑助理"
  
  try {
    const response = await axios.get(`/api/v1/dialog/${row.id}`)
    if (response.data.code === 0) {
      const data = response.data.data
      editForm.value = {
        id: data.id,
        name: data.name,
        description: data.description,
        tenant_id: data.tenant_id,
        llm_id: data.llm_id,
        kb_ids: data.kb_ids || [],
        prompt_config: data.prompt_config || {
          system: "",
          prologue: "",
          empty_response: "",
          parameters: []
        },
        llm_setting: data.llm_setting || {
          temperature: 0.1,
          top_p: 0.3,
          max_tokens: 512
        },
        top_n: data.top_n || 6,
        top_k: data.top_k || 1024,
        similarity_threshold: data.similarity_threshold || 0.1,
        vector_similarity_weight: data.vector_similarity_weight || 0.3,
        rerank_id: data.rerank_id || ""
      }
      editDialogVisible.value = true
    }
  } catch (error) {
    console.error("获取助理详情失败:", error)
    ElMessage.error("获取助理详情失败")
  }
}

/**
 * 保存助理
 */
async function handleSave() {
  try {
    await editFormRef.value?.validate()
    
    const data = { ...editForm.value }
    
    if (isEditing.value && data.id) {
      // 更新
      const response = await axios.put(`/api/v1/dialog/${data.id}`, data)
      if (response.data.code === 0) {
        ElMessage.success("更新成功")
        editDialogVisible.value = false
        getDialogList()
      } else {
        ElMessage.error(response.data.message || "更新失败")
      }
    } else {
      // 创建
      const response = await axios.post("/api/v1/dialog", data)
      if (response.data.code === 0) {
        ElMessage.success("创建成功")
        editDialogVisible.value = false
        getDialogList()
      } else {
        ElMessage.error(response.data.message || "创建失败")
      }
    }
  } catch (error) {
    console.error("保存助理失败:", error)
  }
}

/**
 * 删除助理
 */
async function handleDelete(row: DialogData) {
  try {
    await ElMessageBox.confirm(`确定要删除助理 "${row.name}" 吗？`, "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    })
    
    const response = await axios.delete(`/api/v1/dialog/${row.id}`)
    if (response.data.code === 0) {
      ElMessage.success("删除成功")
      getDialogList()
    } else {
      ElMessage.error(response.data.message || "删除失败")
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除助理失败:", error)
      ElMessage.error("删除助理失败")
    }
  }
}

/**
 * 页码改变
 */
function handleCurrentChange(val: number) {
  currentPage.value = val
  getDialogList()
}

/**
 * 每页条数改变
 */
function handleSizeChange(val: number) {
  pageSize.value = val
  currentPage.value = 1
  getDialogList()
}

/**
 * 搜索
 */
function handleSearch() {
  currentPage.value = 1
  getDialogList()
}

/**
 * 格式化时间
 */
function formatTime(timestamp: number) {
  if (!timestamp) return ""
  const date = new Date(timestamp)
  return date.toLocaleString("zh-CN")
}

/**
 * 格式化LLM显示
 */
function formatLlm(llmId: string) {
  if (!llmId) return "-"
  // 如果包含@，显示模型名和厂商
  if (llmId.includes("@")) {
    return llmId
  }
  return llmId
}

// 初始化
onMounted(() => {
  getDefaultDialog()
  getTenantList()
  getKnowledgebaseList()
  getLlmList()
  getDialogList()
})
</script>

<template>
  <div class="app-container">
    <el-card shadow="never">
      <!-- 搜索栏 -->
      <div class="toolbar">
        <div class="left">
          <el-input
            v-model="searchName"
            placeholder="搜索助理名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
          <el-button type="primary" @click="handleSearch">搜索</el-button>
        </div>
        <div class="right">
          <el-button type="primary" :icon="Plus" @click="handleAdd">新增助理</el-button>
          <el-button :icon="Refresh" @click="getDialogList">刷新</el-button>
        </div>
      </div>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="dialogList" border style="width: 100%">
        <el-table-column label="默认" width="60" align="center">
          <template #default="{ row }">
            <el-button
              :icon="row.is_default ? StarFilled : Star"
              :type="row.is_default ? 'warning' : 'default'"
              link
              @click="setDefaultDialog(row.id)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="name" label="助理名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="tenant_name" label="所属用户" width="150" />
        <el-table-column label="对话模型" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatLlm(row.llm_id) }}
          </template>
        </el-table-column>
        <el-table-column label="知识库" width="200">
          <template #default="{ row }">
            <template v-if="row.kb_names && row.kb_names.length">
              <el-tag v-for="name in row.kb_names.slice(0, 2)" :key="name" size="small" style="margin-right: 4px">
                {{ name }}
              </el-tag>
              <span v-if="row.kb_names.length > 2">+{{ row.kb_names.length - 2 }}</span>
            </template>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button :icon="Edit" type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button :icon="Delete" type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" :title="editDialogTitle" width="700px" destroy-on-close>
      <el-form ref="editFormRef" :model="editForm" :rules="editFormRules" label-width="100px">
        <el-form-item label="助理名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入助理名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editForm.description" type="textarea" rows="2" placeholder="请输入描述" />
        </el-form-item>
        <!-- 以下字段隐藏，由前台用户选择 -->
        <el-form-item label="所属用户" prop="tenant_id" style="display: none">
          <el-select v-model="editForm.tenant_id" placeholder="请选择用户" filterable style="width: 100%">
            <el-option
              v-for="tenant in tenantList"
              :key="tenant.id"
              :label="tenant.name"
              :value="tenant.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="对话模型" prop="llm_id" style="display: none">
          <el-select v-model="editForm.llm_id" placeholder="请选择模型" filterable style="width: 100%">
            <el-option
              v-for="llm in llmList"
              :key="`${llm.llm_name}@${llm.llm_factory}`"
              :label="`${llm.llm_name} (${llm.llm_factory})`"
              :value="`${llm.llm_name}@${llm.llm_factory}`"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联知识库">
          <el-select v-model="editForm.kb_ids" multiple placeholder="请选择知识库" filterable style="width: 100%">
            <el-option
              v-for="kb in knowledgebaseList"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </el-form-item>
        
        <el-divider content-position="left">高级设置</el-divider>
        
        <el-form-item label="开场白">
          <el-input
            v-model="editForm.prompt_config!.prologue"
            type="textarea"
            rows="2"
            placeholder="助理的开场白"
          />
        </el-form-item>
        <el-form-item label="系统提示词">
          <template #label>
            <span>系统提示词</span>
            <el-tooltip placement="top">
              <template #content>
                <div style="max-width: 300px">
                  <p><strong>{knowledge}</strong> 是一个占位符，系统会自动替换为从知识库检索到的相关内容。</p>
                  <p>当用户提问时，系统会：</p>
                  <p>1. 从知识库检索相关文档片段</p>
                  <p>2. 将检索结果填充到 {knowledge} 位置</p>
                  <p>3. 将完整提示词发送给 LLM 生成回答</p>
                </div>
              </template>
              <el-icon style="margin-left: 4px; cursor: help"><QuestionFilled /></el-icon>
            </el-tooltip>
          </template>
          <el-input
            v-model="editForm.prompt_config!.system"
            type="textarea"
            rows="4"
            placeholder="系统提示词，使用 {knowledge} 作为知识库内容占位符"
          />
        </el-form-item>
        <el-form-item label="空结果响应">
          <el-input
            v-model="editForm.prompt_config!.empty_response"
            placeholder="当知识库未找到答案时的响应"
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Temperature">
              <el-slider v-model="editForm.llm_setting!.temperature" :min="0" :max="1" :step="0.1" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Top P">
              <el-slider v-model="editForm.llm_setting!.top_p" :min="0" :max="1" :step="0.1" show-input />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Top N">
              <el-input-number v-model="editForm.top_n" :min="1" :max="20" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="相似度阈值">
              <el-slider v-model="editForm.similarity_threshold" :min="0" :max="1" :step="0.05" show-input />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
.toolbar .left {
  display: flex;
  gap: 12px;
}
.toolbar .right {
  display: flex;
  gap: 12px;
}
.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
