/**
 * 角色管理 API
 */
import { request } from "@/http/axios"

export interface RoleData {
    id?: string
    name: string
    description?: string
    isDefault?: boolean
    status?: string
    createTime?: string
    updateTime?: string
}

export interface RoleUser {
    id: string
    username: string
    email: string
    createTime: string
}

/**
 * 获取角色列表（分页）
 */
export function getRolesApi(params: {
    currentPage: number
    size: number
    name?: string
    sort_by?: string
    sort_order?: string
}) {
    return request<{ list: RoleData[]; total: number }>({
        url: "api/v1/roles",
        method: "get",
        params
    })
}

/**
 * 获取所有启用的角色（用于下拉选择）
 */
export function getAllRolesApi() {
    return request<RoleData[]>({
        url: "api/v1/roles/all",
        method: "get"
    })
}

/**
 * 创建角色
 */
export function createRoleApi(data: { name: string; description?: string }) {
    return request({
        url: "api/v1/roles",
        method: "post",
        data
    })
}

/**
 * 更新角色
 */
export function updateRoleApi(roleId: string, data: { name?: string; description?: string; status?: string }) {
    return request({
        url: `api/v1/roles/${roleId}`,
        method: "put",
        data
    })
}

/**
 * 删除角色
 */
export function deleteRoleApi(roleId: string) {
    return request({
        url: `api/v1/roles/${roleId}`,
        method: "delete"
    })
}

/**
 * 设置为默认角色
 */
export function setDefaultRoleApi(roleId: string) {
    return request({
        url: `api/v1/roles/${roleId}/set-default`,
        method: "post"
    })
}

/**
 * 取消默认角色
 */
export function unsetDefaultRoleApi(roleId: string) {
    return request({
        url: `api/v1/roles/${roleId}/unset-default`,
        method: "post"
    })
}

/**
 * 获取角色下的用户列表
 */
export function getRoleUsersApi(roleId: string, params: { currentPage: number; size: number }) {
    return request<{ list: RoleUser[]; total: number }>({
        url: `api/v1/roles/${roleId}/users`,
        method: "get",
        params
    })
}

/**
 * 获取用户的角色
 */
export function getUserRolesApi(userId: string) {
    return request<RoleData[]>({
        url: `api/v1/users/${userId}/roles`,
        method: "get"
    })
}

/**
 * 设置用户的角色
 */
export function setUserRolesApi(userId: string, roleIds: string[]) {
    return request({
        url: `api/v1/users/${userId}/roles`,
        method: "put",
        data: { role_ids: roleIds }
    })
}

