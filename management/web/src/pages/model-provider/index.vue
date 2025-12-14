<script lang="ts" setup>
import type { Factory, MyLlmGroup } from "@@/apis/llm-providers/type"
import { getFactoriesApi, getMyLlmsApi, setApiKeyApi, addLlmApi, deleteLlmApi, deleteFactoryApi } from "@@/apis/llm-providers"
import { IconMap, LLMFactory, isLocalLlmFactory, isSpecialFormFactory } from "@@/constants/llm"
import { Refresh, Delete, Plus, Setting, MoreFilled } from "@element-plus/icons-vue"

defineOptions({
  name: "ModelProvider"
})

const loading = ref<boolean>(false)

// 数据状态
const factoryList = ref<Factory[]>([])
const myLlms = ref<Record<string, MyLlmGroup>>({})
const activeNames = ref<string[]>(["added", "toAdd"])

// 对话框状态
const apiKeyDialogVisible = ref<boolean>(false)
const ollamaDialogVisible = ref<boolean>(false)
const volcEngineDialogVisible = ref<boolean>(false)
const hunyuanDialogVisible = ref<boolean>(false)
const tencentCloudDialogVisible = ref<boolean>(false)
const bedrockDialogVisible = ref<boolean>(false)
const googleDialogVisible = ref<boolean>(false)
const sparkDialogVisible = ref<boolean>(false)
const yiyanDialogVisible = ref<boolean>(false)
const fishAudioDialogVisible = ref<boolean>(false)
const azureDialogVisible = ref<boolean>(false)

const currentFactory = ref<string>("")
const dialogLoading = ref<boolean>(false)

// 表单数据
const apiKeyForm = reactive({
  api_key: "",
  base_url: ""
})

const ollamaForm = reactive({
  model_type: "embedding",
  llm_name: "",
  api_base: "",
  api_key: "",
  max_tokens: 4096,
  vision: false
})

const volcEngineForm = reactive({
  model_type: "chat",
  llm_name: "",
  endpoint_id: "",
  ark_api_key: "",
  max_tokens: 4096
})

const hunyuanForm = reactive({
  hunyuan_sid: "",
  hunyuan_sk: ""
})

const tencentCloudForm = reactive({
  tencent_cloud_sid: "",
  tencent_cloud_sk: ""
})

const bedrockForm = reactive({
  model_type: "chat",
  llm_name: "",
  bedrock_ak: "",
  bedrock_sk: "",
  bedrock_region: "",
  max_tokens: 4096
})

const googleForm = reactive({
  model_type: "chat",
  llm_name: "",
  google_project_id: "",
  google_region: "",
  google_service_account_key: "",
  max_tokens: 4096
})

const sparkForm = reactive({
  model_type: "chat",
  llm_name: "",
  spark_api_password: "",
  spark_app_id: "",
  spark_api_secret: "",
  spark_api_key: "",
  max_tokens: 4096
})

const yiyanForm = reactive({
  model_type: "chat",
  llm_name: "",
  yiyan_ak: "",
  yiyan_sk: "",
  max_tokens: 4096
})

const fishAudioForm = reactive({
  model_type: "tts",
  llm_name: "",
  fish_audio_ak: "",
  fish_audio_refid: "",
  max_tokens: 4096
})

const azureForm = reactive({
  model_type: "embedding",
  llm_name: "gpt-3.5-turbo",
  api_base: "",
  api_key: "",
  api_version: "2024-02-01",
  max_tokens: 4096,
  vision: false
})

// Bedrock 区域列表
const bedrockRegions = [
  'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
  'ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2',
  'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3'
]

// 模型类型选项
const modelTypeOptions = [
  { value: "chat", label: "chat" },
  { value: "embedding", label: "embedding" },
  { value: "rerank", label: "rerank" },
  { value: "image2text", label: "image2text" },
  { value: "speech2text", label: "sequence2text" },
  { value: "tts", label: "tts" }
]

// 获取图标路径
function getIconPath(factory: string): string {
  const iconName = IconMap[factory] || factory.toLowerCase().replace(/\s+/g, '-')
  return `/src/assets/svg/llm/${iconName}.svg`
}

// 加载数据
async function loadData() {
  loading.value = true
  try {
    const [factoriesRes, myLlmsRes] = await Promise.all([
      getFactoriesApi(),
      getMyLlmsApi()
    ])
    factoryList.value = factoriesRes.data || []
    myLlms.value = myLlmsRes.data || {}
  } catch (error) {
    console.error("加载数据失败:", error)
    ElMessage.error("加载数据失败")
  } finally {
    loading.value = false
  }
}

// 已添加的模型列表
const addedModels = computed(() => {
  return Object.entries(myLlms.value).map(([name, group]) => ({
    name,
    tags: group.tags,
    llm: group.llm
  }))
})

// 待添加的工厂列表 (排除已添加的)
const toAddFactories = computed(() => {
  const addedNames = new Set(Object.keys(myLlms.value))
  return factoryList.value.filter(f => !addedNames.has(f.name))
})

// 展开的模型列表
const expandedFactories = ref<Set<string>>(new Set())

function toggleExpand(factoryName: string) {
  if (expandedFactories.value.has(factoryName)) {
    expandedFactories.value.delete(factoryName)
  } else {
    expandedFactories.value.add(factoryName)
  }
}

// 打开添加模型对话框
function handleAddModel(factoryName: string) {
  currentFactory.value = factoryName
  
  if (isLocalLlmFactory(factoryName)) {
    resetOllamaForm()
    ollamaDialogVisible.value = true
  } else if (factoryName === LLMFactory.VolcEngine) {
    resetVolcEngineForm()
    volcEngineDialogVisible.value = true
  } else if (factoryName === LLMFactory.TencentHunYuan) {
    resetHunyuanForm()
    hunyuanDialogVisible.value = true
  } else if (factoryName === LLMFactory.TencentCloud) {
    resetTencentCloudForm()
    tencentCloudDialogVisible.value = true
  } else if (factoryName === LLMFactory.Bedrock) {
    resetBedrockForm()
    bedrockDialogVisible.value = true
  } else if (factoryName === LLMFactory.GoogleCloud) {
    resetGoogleForm()
    googleDialogVisible.value = true
  } else if (factoryName === LLMFactory.XunFeiSpark) {
    resetSparkForm()
    sparkDialogVisible.value = true
  } else if (factoryName === LLMFactory.BaiduYiYan) {
    resetYiyanForm()
    yiyanDialogVisible.value = true
  } else if (factoryName === LLMFactory.FishAudio) {
    resetFishAudioForm()
    fishAudioDialogVisible.value = true
  } else if (factoryName === LLMFactory.AzureOpenAI) {
    resetAzureForm()
    azureDialogVisible.value = true
  } else {
    // 简单的 API Key 表单
    resetApiKeyForm()
    apiKeyDialogVisible.value = true
  }
}

// 重置表单
function resetApiKeyForm() {
  apiKeyForm.api_key = ""
  apiKeyForm.base_url = ""
}

function resetOllamaForm() {
  ollamaForm.model_type = "embedding"
  ollamaForm.llm_name = ""
  ollamaForm.api_base = ""
  ollamaForm.api_key = ""
  ollamaForm.max_tokens = 4096
  ollamaForm.vision = false
}

function resetVolcEngineForm() {
  volcEngineForm.model_type = "chat"
  volcEngineForm.llm_name = ""
  volcEngineForm.endpoint_id = ""
  volcEngineForm.ark_api_key = ""
  volcEngineForm.max_tokens = 4096
}

function resetHunyuanForm() {
  hunyuanForm.hunyuan_sid = ""
  hunyuanForm.hunyuan_sk = ""
}

function resetTencentCloudForm() {
  tencentCloudForm.tencent_cloud_sid = ""
  tencentCloudForm.tencent_cloud_sk = ""
}

function resetBedrockForm() {
  bedrockForm.model_type = "chat"
  bedrockForm.llm_name = ""
  bedrockForm.bedrock_ak = ""
  bedrockForm.bedrock_sk = ""
  bedrockForm.bedrock_region = ""
  bedrockForm.max_tokens = 4096
}

function resetGoogleForm() {
  googleForm.model_type = "chat"
  googleForm.llm_name = ""
  googleForm.google_project_id = ""
  googleForm.google_region = ""
  googleForm.google_service_account_key = ""
  googleForm.max_tokens = 4096
}

function resetSparkForm() {
  sparkForm.model_type = "chat"
  sparkForm.llm_name = ""
  sparkForm.spark_api_password = ""
  sparkForm.spark_app_id = ""
  sparkForm.spark_api_secret = ""
  sparkForm.spark_api_key = ""
  sparkForm.max_tokens = 4096
}

function resetYiyanForm() {
  yiyanForm.model_type = "chat"
  yiyanForm.llm_name = ""
  yiyanForm.yiyan_ak = ""
  yiyanForm.yiyan_sk = ""
  yiyanForm.max_tokens = 4096
}

function resetFishAudioForm() {
  fishAudioForm.model_type = "tts"
  fishAudioForm.llm_name = ""
  fishAudioForm.fish_audio_ak = ""
  fishAudioForm.fish_audio_refid = ""
  fishAudioForm.max_tokens = 4096
}

function resetAzureForm() {
  azureForm.model_type = "embedding"
  azureForm.llm_name = "gpt-3.5-turbo"
  azureForm.api_base = ""
  azureForm.api_key = ""
  azureForm.api_version = "2024-02-01"
  azureForm.max_tokens = 4096
  azureForm.vision = false
}

// 提交 API Key
async function submitApiKey() {
  if (!apiKeyForm.api_key) {
    ElMessage.error("请输入 API Key")
    return
  }
  dialogLoading.value = true
  try {
    await setApiKeyApi({
      llm_factory: currentFactory.value,
      api_key: apiKeyForm.api_key,
      base_url: apiKeyForm.base_url
    })
    ElMessage.success("添加成功")
    apiKeyDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Ollama 类型模型
async function submitOllama() {
  if (!ollamaForm.llm_name) {
    ElMessage.error("请输入模型名称")
    return
  }
  dialogLoading.value = true
  try {
    const modelType = ollamaForm.model_type === "chat" && ollamaForm.vision ? "image2text" : ollamaForm.model_type
    await addLlmApi({
      llm_factory: currentFactory.value,
      llm_name: ollamaForm.llm_name,
      model_type: modelType,
      api_key: ollamaForm.api_key || "x",
      api_base: ollamaForm.api_base,
      max_tokens: ollamaForm.max_tokens
    })
    ElMessage.success("添加成功")
    ollamaDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 VolcEngine 模型
async function submitVolcEngine() {
  if (!volcEngineForm.llm_name || !volcEngineForm.endpoint_id || !volcEngineForm.ark_api_key) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    await addLlmApi({
      llm_factory: currentFactory.value,
      llm_name: volcEngineForm.llm_name,
      model_type: volcEngineForm.model_type,
      endpoint_id: volcEngineForm.endpoint_id,
      ark_api_key: volcEngineForm.ark_api_key,
      max_tokens: volcEngineForm.max_tokens
    })
    ElMessage.success("添加成功")
    volcEngineDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Hunyuan
async function submitHunyuan() {
  if (!hunyuanForm.hunyuan_sid || !hunyuanForm.hunyuan_sk) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    await setApiKeyApi({
      llm_factory: currentFactory.value,
      api_key: JSON.stringify({
        hunyuan_sid: hunyuanForm.hunyuan_sid,
        hunyuan_sk: hunyuanForm.hunyuan_sk
      })
    })
    ElMessage.success("添加成功")
    hunyuanDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Tencent Cloud
async function submitTencentCloud() {
  if (!tencentCloudForm.tencent_cloud_sid || !tencentCloudForm.tencent_cloud_sk) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    await setApiKeyApi({
      llm_factory: currentFactory.value,
      api_key: JSON.stringify({
        tencent_cloud_sid: tencentCloudForm.tencent_cloud_sid,
        tencent_cloud_sk: tencentCloudForm.tencent_cloud_sk
      })
    })
    ElMessage.success("添加成功")
    tencentCloudDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Bedrock
async function submitBedrock() {
  if (!bedrockForm.llm_name || !bedrockForm.bedrock_ak || !bedrockForm.bedrock_sk || !bedrockForm.bedrock_region) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    await addLlmApi({
      llm_factory: currentFactory.value,
      llm_name: bedrockForm.llm_name,
      model_type: bedrockForm.model_type,
      bedrock_ak: bedrockForm.bedrock_ak,
      bedrock_sk: bedrockForm.bedrock_sk,
      bedrock_region: bedrockForm.bedrock_region,
      max_tokens: bedrockForm.max_tokens
    })
    ElMessage.success("添加成功")
    bedrockDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Google Cloud
async function submitGoogle() {
  if (!googleForm.llm_name || !googleForm.google_project_id || !googleForm.google_region || !googleForm.google_service_account_key) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    await addLlmApi({
      llm_factory: currentFactory.value,
      llm_name: googleForm.llm_name,
      model_type: googleForm.model_type,
      google_project_id: googleForm.google_project_id,
      google_region: googleForm.google_region,
      google_service_account_key: googleForm.google_service_account_key,
      max_tokens: googleForm.max_tokens
    })
    ElMessage.success("添加成功")
    googleDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Spark
async function submitSpark() {
  dialogLoading.value = true
  try {
    if (sparkForm.model_type === "chat") {
      if (!sparkForm.spark_api_password) {
        ElMessage.error("请填写 API Password")
        return
      }
      await addLlmApi({
        llm_factory: currentFactory.value,
        llm_name: sparkForm.llm_name,
        model_type: sparkForm.model_type,
        spark_api_password: sparkForm.spark_api_password,
        max_tokens: sparkForm.max_tokens
      })
    } else {
      if (!sparkForm.spark_app_id || !sparkForm.spark_api_secret || !sparkForm.spark_api_key) {
        ElMessage.error("请填写完整信息")
        return
      }
      await addLlmApi({
        llm_factory: currentFactory.value,
        llm_name: sparkForm.llm_name,
        model_type: sparkForm.model_type,
        spark_app_id: sparkForm.spark_app_id,
        spark_api_secret: sparkForm.spark_api_secret,
        spark_api_key: sparkForm.spark_api_key,
        max_tokens: sparkForm.max_tokens
      })
    }
    ElMessage.success("添加成功")
    sparkDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Yiyan
async function submitYiyan() {
  if (!yiyanForm.llm_name || !yiyanForm.yiyan_ak || !yiyanForm.yiyan_sk) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    await addLlmApi({
      llm_factory: currentFactory.value,
      llm_name: yiyanForm.llm_name,
      model_type: yiyanForm.model_type,
      yiyan_ak: yiyanForm.yiyan_ak,
      yiyan_sk: yiyanForm.yiyan_sk,
      max_tokens: yiyanForm.max_tokens
    })
    ElMessage.success("添加成功")
    yiyanDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 FishAudio
async function submitFishAudio() {
  if (!fishAudioForm.llm_name || !fishAudioForm.fish_audio_ak || !fishAudioForm.fish_audio_refid) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    await addLlmApi({
      llm_factory: currentFactory.value,
      llm_name: fishAudioForm.llm_name,
      model_type: fishAudioForm.model_type,
      fish_audio_ak: fishAudioForm.fish_audio_ak,
      fish_audio_refid: fishAudioForm.fish_audio_refid,
      max_tokens: fishAudioForm.max_tokens
    })
    ElMessage.success("添加成功")
    fishAudioDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 提交 Azure
async function submitAzure() {
  if (!azureForm.llm_name || !azureForm.api_base) {
    ElMessage.error("请填写完整信息")
    return
  }
  dialogLoading.value = true
  try {
    const modelType = azureForm.model_type === "chat" && azureForm.vision ? "image2text" : azureForm.model_type
    await addLlmApi({
      llm_factory: currentFactory.value,
      llm_name: azureForm.llm_name,
      model_type: modelType,
      api_base: azureForm.api_base,
      api_key: azureForm.api_key,
      api_version: azureForm.api_version,
      max_tokens: azureForm.max_tokens
    })
    ElMessage.success("添加成功")
    azureDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error("添加失败:", error)
  } finally {
    dialogLoading.value = false
  }
}

// 删除单个模型
function handleDeleteLlm(factoryName: string, llmName: string) {
  ElMessageBox.confirm(`确认删除模型 ${llmName}？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(async () => {
    try {
      await deleteLlmApi({ llm_factory: factoryName, llm_name: llmName })
      ElMessage.success("删除成功")
      loadData()
    } catch (error) {
      console.error("删除失败:", error)
    }
  })
}

// 删除整个工厂
function handleDeleteFactory(factoryName: string) {
  ElMessageBox.confirm(`确认删除 ${factoryName} 的所有模型配置？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  }).then(async () => {
    try {
      await deleteFactoryApi({ llm_factory: factoryName })
      ElMessage.success("删除成功")
      loadData()
    } catch (error) {
      console.error("删除失败:", error)
    }
  })
}

// 获取真实模型名称 (去除后缀)
function getRealModelName(name: string): string {
  return name.split("___")[0]
}

// 获取按钮文本
function getButtonText(factoryName: string): string {
  if (isLocalLlmFactory(factoryName) || isSpecialFormFactory(factoryName)) {
    return "添加模型"
  }
  return "API-Key"
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="app-container">
    <el-card v-loading="loading" shadow="never">
      <div class="toolbar-wrapper">
        <div class="title">模型提供商配置</div>
        <div>
          <el-tooltip content="刷新">
            <el-button type="primary" :icon="Refresh" circle @click="loadData" />
          </el-tooltip>
        </div>
      </div>

      <el-collapse v-model="activeNames">
        <!-- 已添加的模型 -->
        <el-collapse-item title="已添加的模型" name="added">
          <div v-if="addedModels.length === 0" class="empty-tip">
            暂无已添加的模型
          </div>
          <div v-else class="model-list">
            <el-card v-for="model in addedModels" :key="model.name" class="model-card" shadow="hover">
              <div class="model-header">
                <div class="model-info">
                  <img :src="getIconPath(model.name)" class="model-icon" :alt="model.name" @error="(e: Event) => (e.target as HTMLImageElement).style.display = 'none'" />
                  <div class="model-meta">
                    <div class="model-name">{{ model.name }}</div>
                    <div class="model-tags">{{ model.tags }}</div>
                  </div>
                </div>
                <div class="model-actions">
                  <el-button size="small" @click="handleAddModel(model.name)">
                    <el-icon><Setting /></el-icon>
                    {{ getButtonText(model.name) }}
                  </el-button>
                  <el-button size="small" @click="toggleExpand(model.name)">
                    <el-icon><MoreFilled /></el-icon>
                    显示更多
                  </el-button>
                  <el-button size="small" type="danger" text @click="handleDeleteFactory(model.name)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
              <!-- 展开的模型列表 -->
              <div v-if="expandedFactories.has(model.name)" class="model-detail">
                <div v-for="llm in model.llm" :key="llm.name" class="llm-item">
                  <span class="llm-name">{{ getRealModelName(llm.name) }}</span>
                  <el-tag size="small" type="info">{{ llm.type }}</el-tag>
                  <el-button size="small" type="danger" text @click="handleDeleteLlm(model.name, llm.name)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>
        </el-collapse-item>

        <!-- 待添加的模型 -->
        <el-collapse-item title="待添加的模型" name="toAdd">
          <div v-if="toAddFactories.length === 0" class="empty-tip">
            所有模型已添加
          </div>
          <div v-else class="factory-grid">
            <el-card v-for="factory in toAddFactories" :key="factory.name" class="factory-card" shadow="hover">
              <div class="factory-content">
                <img :src="getIconPath(factory.name)" class="factory-icon" :alt="factory.name" @error="(e: Event) => (e.target as HTMLImageElement).style.display = 'none'" />
                <div class="factory-name">{{ factory.name }}</div>
                <div class="factory-tags">{{ factory.tags }}</div>
              </div>
              <el-divider />
              <el-button type="primary" link @click="handleAddModel(factory.name)">
                <el-icon><Plus /></el-icon>
                添加模型
              </el-button>
            </el-card>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- API Key 对话框 -->
    <el-dialog v-model="apiKeyDialogVisible" :title="`设置 ${currentFactory}`" width="500px">
      <el-form label-width="100px">
        <el-form-item label="API Key" required>
          <el-input v-model="apiKeyForm.api_key" placeholder="请输入 API Key" />
        </el-form-item>
        <el-form-item v-if="currentFactory === 'OpenAI' || currentFactory === 'Azure-OpenAI'" label="Base URL">
          <el-input v-model="apiKeyForm.base_url" placeholder="https://api.openai.com/v1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="apiKeyDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitApiKey">确定</el-button>
      </template>
    </el-dialog>

    <!-- Ollama 类型对话框 -->
    <el-dialog v-model="ollamaDialogVisible" :title="`添加 ${currentFactory} 模型`" width="500px">
      <el-form label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select v-model="ollamaForm.model_type" style="width: 100%">
            <el-option v-for="opt in modelTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="ollamaForm.llm_name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="Base URL" required>
          <el-input v-model="ollamaForm.api_base" placeholder="例如: http://localhost:11434" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="ollamaForm.api_key" placeholder="可选" />
        </el-form-item>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="ollamaForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item v-if="ollamaForm.model_type === 'chat'" label="视觉模型">
          <el-switch v-model="ollamaForm.vision" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ollamaDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitOllama">确定</el-button>
      </template>
    </el-dialog>

    <!-- VolcEngine 对话框 -->
    <el-dialog v-model="volcEngineDialogVisible" title="添加 VolcEngine 模型" width="500px">
      <el-form label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select v-model="volcEngineForm.model_type" style="width: 100%">
            <el-option label="chat" value="chat" />
            <el-option label="embedding" value="embedding" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="volcEngineForm.llm_name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="Endpoint ID" required>
          <el-input v-model="volcEngineForm.endpoint_id" placeholder="请输入 Endpoint ID" />
        </el-form-item>
        <el-form-item label="Ark API Key" required>
          <el-input v-model="volcEngineForm.ark_api_key" placeholder="请输入 Ark API Key" />
        </el-form-item>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="volcEngineForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="volcEngineDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitVolcEngine">确定</el-button>
      </template>
    </el-dialog>

    <!-- Hunyuan 对话框 -->
    <el-dialog v-model="hunyuanDialogVisible" title="添加腾讯混元" width="500px">
      <el-form label-width="120px">
        <el-form-item label="Secret ID" required>
          <el-input v-model="hunyuanForm.hunyuan_sid" placeholder="请输入 Secret ID" />
        </el-form-item>
        <el-form-item label="Secret Key" required>
          <el-input v-model="hunyuanForm.hunyuan_sk" placeholder="请输入 Secret Key" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="hunyuanDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitHunyuan">确定</el-button>
      </template>
    </el-dialog>

    <!-- Tencent Cloud 对话框 -->
    <el-dialog v-model="tencentCloudDialogVisible" title="添加腾讯云" width="500px">
      <el-form label-width="120px">
        <el-form-item label="Secret ID" required>
          <el-input v-model="tencentCloudForm.tencent_cloud_sid" placeholder="请输入 Secret ID" />
        </el-form-item>
        <el-form-item label="Secret Key" required>
          <el-input v-model="tencentCloudForm.tencent_cloud_sk" placeholder="请输入 Secret Key" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tencentCloudDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitTencentCloud">确定</el-button>
      </template>
    </el-dialog>

    <!-- Bedrock 对话框 -->
    <el-dialog v-model="bedrockDialogVisible" title="添加 AWS Bedrock" width="500px">
      <el-form label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select v-model="bedrockForm.model_type" style="width: 100%">
            <el-option label="chat" value="chat" />
            <el-option label="embedding" value="embedding" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="bedrockForm.llm_name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="Access Key" required>
          <el-input v-model="bedrockForm.bedrock_ak" placeholder="请输入 Access Key" />
        </el-form-item>
        <el-form-item label="Secret Key" required>
          <el-input v-model="bedrockForm.bedrock_sk" placeholder="请输入 Secret Key" />
        </el-form-item>
        <el-form-item label="Region" required>
          <el-select v-model="bedrockForm.bedrock_region" style="width: 100%">
            <el-option v-for="region in bedrockRegions" :key="region" :label="region" :value="region" />
          </el-select>
        </el-form-item>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="bedrockForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bedrockDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitBedrock">确定</el-button>
      </template>
    </el-dialog>

    <!-- Google Cloud 对话框 -->
    <el-dialog v-model="googleDialogVisible" title="添加 Google Cloud" width="500px">
      <el-form label-width="150px">
        <el-form-item label="模型类型" required>
          <el-select v-model="googleForm.model_type" style="width: 100%">
            <el-option label="chat" value="chat" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型 ID" required>
          <el-input v-model="googleForm.llm_name" placeholder="请输入模型 ID" />
        </el-form-item>
        <el-form-item label="Project ID" required>
          <el-input v-model="googleForm.google_project_id" placeholder="请输入 Project ID" />
        </el-form-item>
        <el-form-item label="Region" required>
          <el-input v-model="googleForm.google_region" placeholder="例如: us-central1" />
        </el-form-item>
        <el-form-item label="Service Account Key" required>
          <el-input v-model="googleForm.google_service_account_key" type="textarea" :rows="3" placeholder="请输入 Service Account Key" />
        </el-form-item>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="googleForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="googleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitGoogle">确定</el-button>
      </template>
    </el-dialog>

    <!-- Spark 对话框 -->
    <el-dialog v-model="sparkDialogVisible" title="添加讯飞星火" width="500px">
      <el-form label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select v-model="sparkForm.model_type" style="width: 100%">
            <el-option label="chat" value="chat" />
            <el-option label="tts" value="tts" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="sparkForm.llm_name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item v-if="sparkForm.model_type === 'chat'" label="API Password" required>
          <el-input v-model="sparkForm.spark_api_password" placeholder="请输入 API Password" />
        </el-form-item>
        <template v-if="sparkForm.model_type === 'tts'">
          <el-form-item label="App ID" required>
            <el-input v-model="sparkForm.spark_app_id" placeholder="请输入 App ID" />
          </el-form-item>
          <el-form-item label="API Secret" required>
            <el-input v-model="sparkForm.spark_api_secret" placeholder="请输入 API Secret" />
          </el-form-item>
          <el-form-item label="API Key" required>
            <el-input v-model="sparkForm.spark_api_key" placeholder="请输入 API Key" />
          </el-form-item>
        </template>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="sparkForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sparkDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitSpark">确定</el-button>
      </template>
    </el-dialog>

    <!-- Yiyan 对话框 -->
    <el-dialog v-model="yiyanDialogVisible" title="添加百度文心" width="500px">
      <el-form label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select v-model="yiyanForm.model_type" style="width: 100%">
            <el-option label="chat" value="chat" />
            <el-option label="embedding" value="embedding" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="yiyanForm.llm_name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="Access Key" required>
          <el-input v-model="yiyanForm.yiyan_ak" placeholder="请输入 Access Key" />
        </el-form-item>
        <el-form-item label="Secret Key" required>
          <el-input v-model="yiyanForm.yiyan_sk" placeholder="请输入 Secret Key" />
        </el-form-item>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="yiyanForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="yiyanDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitYiyan">确定</el-button>
      </template>
    </el-dialog>

    <!-- FishAudio 对话框 -->
    <el-dialog v-model="fishAudioDialogVisible" title="添加 Fish Audio" width="500px">
      <el-form label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select v-model="fishAudioForm.model_type" style="width: 100%">
            <el-option label="tts" value="tts" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="fishAudioForm.llm_name" placeholder="请输入模型名称" />
        </el-form-item>
        <el-form-item label="API Key" required>
          <el-input v-model="fishAudioForm.fish_audio_ak" placeholder="请输入 API Key" />
        </el-form-item>
        <el-form-item label="Reference ID" required>
          <el-input v-model="fishAudioForm.fish_audio_refid" placeholder="请输入 Reference ID" />
        </el-form-item>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="fishAudioForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fishAudioDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitFishAudio">确定</el-button>
      </template>
    </el-dialog>

    <!-- Azure OpenAI 对话框 -->
    <el-dialog v-model="azureDialogVisible" title="添加 Azure OpenAI" width="500px">
      <el-form label-width="120px">
        <el-form-item label="模型类型" required>
          <el-select v-model="azureForm.model_type" style="width: 100%">
            <el-option label="chat" value="chat" />
            <el-option label="embedding" value="embedding" />
            <el-option label="image2text" value="image2text" />
          </el-select>
        </el-form-item>
        <el-form-item label="Base URL" required>
          <el-input v-model="azureForm.api_base" placeholder="请输入 Base URL" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="azureForm.api_key" placeholder="请输入 API Key" />
        </el-form-item>
        <el-form-item label="模型名称" required>
          <el-input v-model="azureForm.llm_name" placeholder="例如: gpt-3.5-turbo" />
        </el-form-item>
        <el-form-item label="API Version">
          <el-input v-model="azureForm.api_version" placeholder="2024-02-01" />
        </el-form-item>
        <el-form-item label="Max Tokens" required>
          <el-input-number v-model="azureForm.max_tokens" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item v-if="azureForm.model_type === 'chat'" label="视觉模型">
          <el-switch v-model="azureForm.vision" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="azureDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogLoading" @click="submitAzure">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.toolbar-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  .title {
    font-size: 18px;
    font-weight: bold;
  }
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 40px 0;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.model-card {
  .model-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .model-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .model-icon {
    width: 40px;
    height: 40px;
    object-fit: contain;
  }

  .model-meta {
    .model-name {
      font-weight: bold;
      font-size: 16px;
    }

    .model-tags {
      color: #909399;
      font-size: 12px;
    }
  }

  .model-actions {
    display: flex;
    gap: 8px;
  }

  .model-detail {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #ebeef5;

    .llm-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;

      .llm-name {
        flex: 1;
      }
    }
  }
}

.factory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.factory-card {
  text-align: center;

  .factory-content {
    padding: 16px 0;
  }

  .factory-icon {
    width: 48px;
    height: 48px;
    object-fit: contain;
    margin-bottom: 12px;
  }

  .factory-name {
    font-weight: bold;
    margin-bottom: 4px;
  }

  .factory-tags {
    color: #909399;
    font-size: 12px;
  }

  .el-divider {
    margin: 12px 0;
  }
}
</style>
