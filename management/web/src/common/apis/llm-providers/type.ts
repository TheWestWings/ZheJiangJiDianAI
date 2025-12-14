/** LLM 提供商相关类型定义 */

/** 模型工厂 */
export interface Factory {
    name: string
    logo: string
    tags: string
    status: string
    model_types: string[]
}

/** 已配置的模型 */
export interface MyLlm {
    type: string
    name: string
    used_token: number
}

/** 已配置的模型分组 */
export interface MyLlmGroup {
    tags: string
    llm: MyLlm[]
}

/** 模型列表项 */
export interface LlmItem {
    llm_name: string
    model_type: string
    fid: string
    max_tokens?: number
    tags?: string
    available: boolean
}

/** 设置 API Key 参数 */
export interface SetApiKeyParams {
    llm_factory: string
    api_key: string
    base_url?: string
}

/** 添加模型参数 */
export interface AddLlmParams {
    llm_factory: string
    llm_name: string
    model_type: string
    api_key?: string
    api_base?: string
    max_tokens?: number
    // VolcEngine
    ark_api_key?: string
    endpoint_id?: string
    // Hunyuan
    hunyuan_sid?: string
    hunyuan_sk?: string
    // Tencent Cloud
    tencent_cloud_sid?: string
    tencent_cloud_sk?: string
    // Bedrock
    bedrock_ak?: string
    bedrock_sk?: string
    bedrock_region?: string
    // Google Cloud
    google_project_id?: string
    google_region?: string
    google_service_account_key?: string
    // Spark
    spark_api_password?: string
    spark_app_id?: string
    spark_api_secret?: string
    spark_api_key?: string
    // BaiduYiyan
    yiyan_ak?: string
    yiyan_sk?: string
    // Fish Audio
    fish_audio_ak?: string
    fish_audio_refid?: string
    // Azure
    api_version?: string
    // Vision
    vision?: boolean
}

/** 删除模型参数 */
export interface DeleteLlmParams {
    llm_factory: string
    llm_name: string
}

/** 删除工厂参数 */
export interface DeleteFactoryParams {
    llm_factory: string
}

/** 通用响应 */
export interface ApiResponse<T = any> {
    code: number
    data: T
    message: string
}

/** 获取工厂列表响应 */
export type FactoriesResponse = ApiResponse<Factory[]>

/** 获取已配置模型响应 */
export type MyLlmsResponse = ApiResponse<Record<string, MyLlmGroup>>

/** 获取模型列表响应 */
export type LlmsListResponse = ApiResponse<Record<string, LlmItem[]>>
