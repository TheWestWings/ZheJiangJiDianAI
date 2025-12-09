<script lang="ts" setup>
import { Star, Edit, Delete, Plus, Refresh, Setting } from "@element-plus/icons-vue"
import axios from "axios"

defineOptions({
  name: "AssistantManagement"
})

// 助理数据类型
interface DialogData {
  id: string
  name: string
  description: string
  icon: string
  tenant_id: string
  llm_id: string
  kb_ids: string[]
  top_n: number
  top_k: number
  similarity_threshold: number
  vector_similarity_weight: number
  rerank_id: string
  llm_setting: {
    temperature?: number
    top_p?: number
    presence_penalty?: number
    frequency_penalty?: number
    max_tokens?: number
  }
  prompt_config: {
    system?: string
    prologue?: string
    empty_response?: string
    quote?: boolean
    cross_language_search?: boolean
    parameters?: Array<{ key: string; optional: boolean }>
  }
  create_time: string
  update_time: string
  is_default?: boolean
}

// 租户数据类型
interface TenantData {
  id: string
  nickname: string
  email: string
}

// 知识库数据类型
interface KnowledgeBaseData {
  id: string
  name: string
}

// 模型数据类型
interface LLMData {
  llm_name: string
  model_type: string
  fid: string
}

// 状态
const loading = ref(false)
const dialogList = ref<DialogData[]>([])
const tenantList = ref<TenantData[]>([])
const knowledgeBaseList = ref<KnowledgeBaseData[]>([])
const llmList = ref<LLMData[]>([])
const defaultDialogId = ref<string | null>(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchName = ref("")

// 配置对话框状态
const configDialogVisible = ref(false)
const configDialogTitle = ref("新建助理")
const isEdit = ref(false)
const activeTab = ref("basic")
const saving = ref(false)

// 当前编辑的助理数据
const currentDialog = ref<Partial<DialogData>>({
  name: "",
  description: "",
  tenant_id: "",
  kb_ids: [],
  llm_id: "",
  top_n: 6,
  top_k: 1024,
  similarity_threshold: 0.1,
  vector_similarity_weight: 0.3,
  rerank_id: "",
  llm_setting: {
    temperature: 0.1,
    top_p: 0.3,
    presence_penalty: 0.4,
    frequency_penalty: 0.7,
    max_tokens: 512
  },
  prompt_config: {
    system: `你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括"知识库中未找到您要的答案！"这句话。回答需要考虑聊天历史。
以下是知识库：
{knowledge}
以上是知识库。`,
    prologue: "您好，我是您的助手，有什么可以帮您？",
    empty_response: "抱歉，知识库中未找到相关内容！",
    quote: true,
    cross_language_search: false,
    parameters: [{ key: "knowledge", optional: false }]
  }
})

/**
 * 获取助理列表
 */
async function getDialogList() {
  loading.value = true
  try {
    const response = await axios.get("/api/v1/dialog", {
      params: {
        page: currentPage.value,
        size: pageSize.value,
        name: searchName.value || undefined
      }
    })
    if (response.data.code === 0) {
      dialogList.value = response.data.data.list || []
      total.value = response.data.data.total || 0

      // 标记默认助理
      dialogList.value.forEach((item) => {
        item.is_default = item.id === defaultDialogId.value
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
      defaultDialogId.value = response.data.data.dialog_id
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
async function getKnowledgeBaseList() {
  try {
    const response = await axios.get("/api/v1/dialog/knowledgebases")
    if (response.data.code === 0) {
      knowledgeBaseList.value = response.data.data || []
    }
  } catch (error) {
    console.error("获取知识库列表失败:", error)
  }
}

/**
 * 获取模型列表
 */
async function getLLMList() {
  try {
    const response = await axios.get("/api/v1/dialog/llms")
    if (response.data.code === 0) {
      llmList.value = response.data.data || []
    }
  } catch (error) {
    console.error("获取模型列表失败:", error)
  }
}

/**
 * 搜索
 */
function handleSearch() {
  currentPage.value = 1
  getDialogList()
}

/**
 * 刷新
 */
function handleRefresh() {
  searchName.value = ""
  currentPage.value = 1
  getDialogList()
}

/**
 * 分页变化
 */
function handlePageChange(page: number) {
  currentPage.value = page
  getDialogList()
}

/**
 * 显示新建对话框
 */
function showAddDialog() {
  configDialogTitle.value = "新建助理"
  isEdit.value = false
  activeTab.value = "basic"
  currentDialog.value = {
    name: "",
    description: "",
    tenant_id: "",
    kb_ids: [],
    llm_id: "",
    top_n: 6,
    top_k: 1024,
    similarity_threshold: 0.1,
    vector_similarity_weight: 0.3,
    rerank_id: "",
    llm_setting: {
      temperature: 0.1,
      top_p: 0.3,
      presence_penalty: 0.4,
      frequency_penalty: 0.7,
      max_tokens: 512
    },
    prompt_config: {
      system: `你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括"知识库中未找到您要的答案！"这句话。回答需要考虑聊天历史。
以下是知识库：
{knowledge}
以上是知识库。`,
      prologue: "您好，我是您的助手，有什么可以帮您？",
      empty_response: "抱歉，知识库中未找到相关内容！",
      quote: true,
      cross_language_search: false,
      parameters: [{ key: "knowledge", optional: false }]
    }
  }
  configDialogVisible.value = true
}

/**
 * 显示编辑对话框
 */
async function showEditDialog(row: DialogData) {
  configDialogTitle.value = "编辑助理"
  isEdit.value = true
  activeTab.value = "basic"

  // 获取助理详情
  try {
    const response = await axios.get(`/api/v1/dialog/${row.id}`)
    if (response.data.code === 0) {
      const data = response.data.data
      currentDialog.value = {
        ...data,
        llm_setting: data.llm_setting || {
          temperature: 0.1,
          top_p: 0.3,
          presence_penalty: 0.4,
          frequency_penalty: 0.7,
          max_tokens: 512
        },
        prompt_config: data.prompt_config || {
          system: "",
          prologue: "",
          empty_response: "",
          quote: true,
          cross_language_search: false,
          parameters: []
        }
      }
      configDialogVisible.value = true
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
  if (!currentDialog.value.name) {
    ElMessage.warning("请输入助理名称")
    return
  }
  if (!currentDialog.value.tenant_id) {
    ElMessage.warning("请选择所属用户")
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await axios.put(`/api/v1/dialog/${currentDialog.value.id}`, currentDialog.value)
      ElMessage.success("更新成功")
    } else {
      await axios.post("/api/v1/dialog", currentDialog.value)
      ElMessage.success("创建成功")
    }
    configDialogVisible.value = false
    getDialogList()
  } catch (error) {
    console.error("保存失败:", error)
    ElMessage.error("保存失败")
  } finally {
    saving.value = false
  }
}

/**
 * 删除助理
 */
async function handleDelete(row: DialogData) {
  try {
    await ElMessageBox.confirm("确定要删除该助理吗？", "提示", {
      type: "warning"
    })
    await axios.delete(`/api/v1/dialog/${row.id}`)
    ElMessage.success("删除成功")
    getDialogList()
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error)
      ElMessage.error("删除失败")
    }
  }
}

/**
 * 设置默认助理
 */
async function handleSetDefault(row: DialogData) {
  try {
    await axios.post(`/api/v1/dialog/${row.id}/set-default`)
    defaultDialogId.value = row.id
    ElMessage.success("设置成功")
    getDialogList()
  } catch (error) {
    console.error("设置默认助理失败:", error)
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
  await Promise.all([
    getDefaultDialog(),
    getTenantList(),
    getKnowledgeBaseList(),
    getLLMList()
  ])
  await getDialogList()
})
</script>

<template>
  <div class="app-container">
    <!-- 搜索栏 -->
    <el-card shadow="hover" class="search-wrapper">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input v-model="searchName" placeholder="请输入助理名称" clearable @keyup.enter="handleSearch" />
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
          <el-button type="primary" :icon="Plus" @click="showAddDialog">
            新建助理
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="hover" class="table-wrapper">
      <el-table v-loading="loading" :data="dialogList" border stripe>
        <el-table-column label="默认" width="70" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.is_default" color="#f7ba2a" :size="20">
              <Star />
            </el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="助理名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="知识库数量" width="100" align="center">
          <template #default="{ row }">
            {{ Array.isArray(row.kb_ids) ? row.kb_ids.length : 0 }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
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
            <el-button type="primary" size="small" :icon="Setting" @click="showEditDialog(row)">
              配置
            </el-button>
            <el-button type="danger" size="small" :icon="Delete" @click="handleDelete(row)">
              删除
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

    <!-- 配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      :title="configDialogTitle"
      width="800px"
      destroy-on-close
    >
      <el-tabs v-model="activeTab">
        <!-- 基础设置 -->
        <el-tab-pane label="基础设置" name="basic">
          <el-form :model="currentDialog" label-width="120px">
            <el-form-item label="助理名称" required>
              <el-input v-model="currentDialog.name" placeholder="请输入助理名称" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input
                v-model="currentDialog.description"
                type="textarea"
                :rows="2"
                placeholder="请输入助理描述"
              />
            </el-form-item>
            <el-form-item label="所属用户" required>
              <el-select v-model="currentDialog.tenant_id" placeholder="请选择用户" style="width: 100%">
                <el-option
                  v-for="tenant in tenantList"
                  :key="tenant.id"
                  :label="tenant.nickname || tenant.email"
                  :value="tenant.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="关联知识库">
              <el-select
                v-model="currentDialog.kb_ids"
                multiple
                placeholder="请选择知识库"
                style="width: 100%"
              >
                <el-option
                  v-for="kb in knowledgeBaseList"
                  :key="kb.id"
                  :label="kb.name"
                  :value="kb.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="空回答响应">
              <el-input
                v-model="currentDialog.prompt_config!.empty_response"
                placeholder="当知识库无相关内容时的响应"
              />
            </el-form-item>
            <el-form-item label="开场白">
              <el-input
                v-model="currentDialog.prompt_config!.prologue"
                type="textarea"
                :rows="2"
                placeholder="助理开场白"
              />
            </el-form-item>
            <el-form-item label="显示引用">
              <el-switch v-model="currentDialog.prompt_config!.quote" />
            </el-form-item>
            <el-form-item label="跨语言搜索">
              <el-switch v-model="currentDialog.prompt_config!.cross_language_search" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 提示词设置 -->
        <el-tab-pane label="提示词设置" name="prompt">
          <el-form :model="currentDialog" label-width="120px">
            <el-form-item label="系统提示词">
              <el-input
                v-model="currentDialog.prompt_config!.system"
                type="textarea"
                :rows="10"
                placeholder="系统提示词，使用 {knowledge} 作为知识库内容的占位符"
              />
            </el-form-item>
            <el-divider />
            <el-form-item label="相似度阈值">
              <el-slider
                v-model="currentDialog.similarity_threshold"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
            </el-form-item>
            <el-form-item label="关键词权重">
              <el-slider
                v-model="currentDialog.vector_similarity_weight"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
              <div class="tip-text">向量相似度权重（0为纯关键词，1为纯向量）</div>
            </el-form-item>
            <el-form-item label="Top N">
              <el-input-number
                v-model="currentDialog.top_n"
                :min="1"
                :max="30"
              />
              <span class="tip-text"> 返回的相关文档数量</span>
            </el-form-item>
            <el-form-item label="Top K">
              <el-input-number
                v-model="currentDialog.top_k"
                :min="1"
                :max="4096"
              />
              <span class="tip-text"> 每个文档的最大token数</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 模型设置 -->
        <el-tab-pane label="模型设置" name="model">
          <el-form :model="currentDialog" label-width="150px">
            <el-form-item label="选择模型">
              <el-select v-model="currentDialog.llm_id" placeholder="请选择模型" style="width: 100%">
                <el-option
                  v-for="llm in llmList"
                  :key="llm.llm_name"
                  :label="llm.llm_name"
                  :value="llm.llm_name"
                />
              </el-select>
            </el-form-item>
            <el-divider />
            <el-form-item label="Temperature（创意度）">
              <el-slider
                v-model="currentDialog.llm_setting!.temperature"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
              <div class="tip-text">值越高回答越有创意，值越低回答越保守</div>
            </el-form-item>
            <el-form-item label="Top P">
              <el-slider
                v-model="currentDialog.llm_setting!.top_p"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
            </el-form-item>
            <el-form-item label="Presence Penalty">
              <el-slider
                v-model="currentDialog.llm_setting!.presence_penalty"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
              <div class="tip-text">值越高越不易重复已说过的话题</div>
            </el-form-item>
            <el-form-item label="Frequency Penalty">
              <el-slider
                v-model="currentDialog.llm_setting!.frequency_penalty"
                :min="0"
                :max="1"
                :step="0.01"
                show-input
              />
              <div class="tip-text">值越高越不易重复已说过的词语</div>
            </el-form-item>
            <el-form-item label="Max Tokens">
              <el-input-number
                v-model="currentDialog.llm_setting!.max_tokens"
                :min="1"
                :max="8192"
              />
              <span class="tip-text"> 最大输出token数</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="configDialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          确定
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
