/** LLM 提供商 API */
import type * as LlmProviders from "./type"
import { request } from "@/http/axios"

/** 获取所有可用的模型工厂列表 */
export function getFactoriesApi() {
    return request<LlmProviders.FactoriesResponse>({
        url: "api/v1/llm-providers/factories",
        method: "get"
    })
}

/** 获取已配置的模型列表 */
export function getMyLlmsApi() {
    return request<LlmProviders.MyLlmsResponse>({
        url: "api/v1/llm-providers/my-llms",
        method: "get"
    })
}

/** 设置 API Key，批量导入模型 */
export function setApiKeyApi(params: LlmProviders.SetApiKeyParams) {
    return request<LlmProviders.ApiResponse>({
        url: "api/v1/llm-providers/set-api-key",
        method: "post",
        data: params
    })
}

/** 添加单个自定义模型 */
export function addLlmApi(params: LlmProviders.AddLlmParams) {
    return request<LlmProviders.ApiResponse>({
        url: "api/v1/llm-providers/add-llm",
        method: "post",
        data: params
    })
}

/** 删除单个模型 */
export function deleteLlmApi(params: LlmProviders.DeleteLlmParams) {
    return request<LlmProviders.ApiResponse>({
        url: "api/v1/llm-providers/delete-llm",
        method: "post",
        data: params
    })
}

/** 删除整个工厂的所有模型配置 */
export function deleteFactoryApi(params: LlmProviders.DeleteFactoryParams) {
    return request<LlmProviders.ApiResponse>({
        url: "api/v1/llm-providers/delete-factory",
        method: "post",
        data: params
    })
}

/** 获取模型列表 */
export function listLlmsApi(modelType?: string) {
    return request<LlmProviders.LlmsListResponse>({
        url: "api/v1/llm-providers/list",
        method: "get",
        params: modelType ? { model_type: modelType } : {}
    })
}

export type * from "./type"
