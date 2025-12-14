export interface CreateOrUpdateTableRequestData {
    id?: string
    username: string
    email?: string
    password?: string
    gender?: string
    department?: string
    phone?: string
}

export interface TableRequestData {
    /** 当前页码 */
    currentPage: number
    /** 查询条数 */
    size: number
    /** 查询参数：姓名 */
    username?: string
    /** 查询参数：学号/工号 */
    email?: string
    /** 排序字段 */
    sort_by: string
    /** 排序方式 */
    sort_order: string
}

export interface TableData {
    id: string
    username: string
    email: string
    gender?: string
    department?: string
    phone?: string
    createTime: string
    updateTime: string
    is_system_admin?: boolean
    is_super_admin?: boolean
}

export type TableResponseData = ApiResponseData<{
    list: TableData[]
    total: number
}>
