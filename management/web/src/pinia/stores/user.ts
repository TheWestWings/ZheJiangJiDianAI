import { pinia } from "@/pinia"
import { resetRouter } from "@/router"
import { routerConfig } from "@/router/config"
import { getCurrentUserApi } from "@@/apis/users"
import { setToken as _setToken, getToken, removeToken } from "@@/utils/cache/cookies"
import { useSettingsStore } from "./settings"
import { useTagsViewStore } from "./tags-view"

export const useUserStore = defineStore("user", () => {
    const token = ref<string>(getToken() || "")
    const roles = ref<string[]>([])
    const username = ref<string>("")
    const avatar = ref<string>("https://pic1.zhimg.com/v2-aaf12b68b54b8812e6b449e7368d30cf_l.jpg?source=32738c0c&needBackground=1")
    const is_super_admin = ref<boolean>(false)
    const is_system_admin = ref<boolean>(false)
    const tagsViewStore = useTagsViewStore()
    const settingsStore = useSettingsStore()

    // 初始化时解析已存在的 token
    const initFromToken = () => {
        const currentToken = token.value
        if (currentToken) {
            try {
                const payload = JSON.parse(atob(currentToken.split('.')[1]))
                is_super_admin.value = payload.is_super_admin || false
                is_system_admin.value = payload.is_system_admin || false
            } catch (e) {
                console.error('Failed to parse token on init:', e)
            }
        }
    }

    // 页面加载时自动初始化
    initFromToken()

    // 设置 Token
    const setToken = (value: string) => {
        _setToken(value)
        token.value = value
        // 重置 roles，确保路由守卫会重新调用 getInfo
        roles.value = []

        // 尝试从JWT token解析角色信息
        try {
            const payload = JSON.parse(atob(value.split('.')[1]))
            is_super_admin.value = payload.is_super_admin || false
            is_system_admin.value = payload.is_system_admin || false
        } catch (e) {
            console.error('Failed to parse token:', e)
        }
    }

    // 获取用户详情
    const getInfo = async () => {
        const { data } = await getCurrentUserApi()
        username.value = data.username
        // 验证返回的 roles 是否为一个非空数组，否则塞入一个没有任何作用的默认角色，防止路由守卫逻辑进入无限循环
        roles.value = data.roles?.length > 0 ? data.roles : routerConfig.defaultRoles
        // 从 API 获取管理员角色信息（如果存在）
        if (data.is_super_admin !== undefined) {
            is_super_admin.value = data.is_super_admin
        }
        if (data.is_system_admin !== undefined) {
            is_system_admin.value = data.is_system_admin
        }
    }

    // 模拟角色变化
    const changeRoles = (role: string) => {
        const newToken = `token-${role}`
        token.value = newToken
        _setToken(newToken)
        // 用刷新页面代替重新登录
        location.reload()
    }

    // 登出
    const logout = () => {
        removeToken()
        token.value = ""
        roles.value = []
        is_super_admin.value = false
        is_system_admin.value = false
        resetRouter()
        resetTagsView()
    }

    // 重置 Token
    const resetToken = () => {
        removeToken()
        token.value = ""
        roles.value = []
        is_super_admin.value = false
        is_system_admin.value = false
    }

    // 重置 Visited Views 和 Cached Views
    const resetTagsView = () => {
        if (!settingsStore.cacheTagsView) {
            tagsViewStore.delAllVisitedViews()
            tagsViewStore.delAllCachedViews()
        }
    }

    return { token, roles, username, avatar, is_super_admin, is_system_admin, setToken, getInfo, changeRoles, logout, resetToken }
})

/**
 * @description 在 SPA 应用中可用于在 pinia 实例被激活前使用 store
 * @description 在 SSR 应用中可用于在 setup 外使用 store
 */
export function useUserStoreOutside() {
    return useUserStore(pinia)
}
