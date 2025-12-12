"""
角色管理服务层

提供角色的CRUD操作、用户角色管理、默认角色处理等功能
"""
import mysql.connector
import pytz
from datetime import datetime
from database import DB_CONFIG

def generate_uuid():
    """生成UUID"""
    import uuid
    return uuid.uuid4().hex


def get_roles_with_pagination(current_page, page_size, name='', sort_by="create_time", sort_order="desc"):
    """获取角色列表（分页）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 构建WHERE子句
        where_clauses = []
        params = []
        
        if name:
            where_clauses.append("name LIKE %s")
            params.append(f"%{name}%")
        
        where_sql = "WHERE " + (" AND ".join(where_clauses) if where_clauses else "1=1")
        
        # 验证排序字段
        valid_sort_fields = ["name", "create_time", "create_date", "is_default"]
        if sort_by not in valid_sort_fields:
            sort_by = "create_time"
        
        sort_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM role {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 分页查询
        offset = (current_page - 1) * page_size
        query = f"""
        SELECT id, name, description, is_default, status, create_date, update_date
        FROM role
        {where_sql}
        {sort_clause}
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [page_size, offset])
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 格式化结果
        formatted_roles = []
        for role in results:
            formatted_roles.append({
                "id": role["id"],
                "name": role["name"],
                "description": role["description"] or "",
                "isDefault": role["is_default"] == 1,
                "status": role["status"],
                "createTime": role["create_date"].strftime("%Y-%m-%d %H:%M:%S") if role["create_date"] else "",
                "updateTime": role["update_date"].strftime("%Y-%m-%d %H:%M:%S") if role["update_date"] else "",
            })
        
        return formatted_roles, total
        
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return [], 0


def get_all_roles():
    """获取所有启用的角色（用于下拉选择）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT id, name, is_default
        FROM role
        WHERE status = '1'
        ORDER BY is_default DESC, name ASC
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [{"id": r["id"], "name": r["name"], "isDefault": r["is_default"] == 1} for r in results]
        
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return []


def create_role(role_data):
    """创建角色"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        role_id = generate_uuid()
        name = role_data.get("name")
        description = role_data.get("description", "")
        
        # 获取当前时间
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        target_tz = pytz.timezone('Asia/Shanghai')
        local_dt = utc_now.astimezone(target_tz)
        create_time = int(local_dt.timestamp() * 1000)
        current_date = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
        INSERT INTO role (id, name, description, is_default, status, create_time, create_date, update_time, update_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (role_id, name, description, 0, '1', create_time, current_date, create_time, current_date))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, role_id
        
    except mysql.connector.Error as err:
        print(f"创建角色错误: {err}")
        return False, str(err)


def update_role(role_id, role_data):
    """更新角色"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        name = role_data.get("name")
        description = role_data.get("description", "")
        status = role_data.get("status", "1")
        
        # 获取当前时间
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        target_tz = pytz.timezone('Asia/Shanghai')
        local_dt = utc_now.astimezone(target_tz)
        update_time = int(local_dt.timestamp() * 1000)
        update_date = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
        UPDATE role 
        SET name = %s, description = %s, status = %s, update_time = %s, update_date = %s
        WHERE id = %s
        """
        cursor.execute(query, (name, description, status, update_time, update_date, role_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"更新角色错误: {err}")
        return False


def delete_role(role_id):
    """删除角色（需先检查是否有用户关联）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 检查是否为默认角色
        cursor.execute("SELECT is_default FROM role WHERE id = %s", (role_id,))
        role = cursor.fetchone()
        if role and role['is_default'] == 1:
            cursor.close()
            conn.close()
            return False, "无法删除默认角色"
        
        # 检查是否有用户关联
        cursor.execute("SELECT COUNT(*) as count FROM user_role WHERE role_id = %s", (role_id,))
        result = cursor.fetchone()
        if result['count'] > 0:
            cursor.close()
            conn.close()
            return False, f"该角色下还有 {result['count']} 个用户，请先解除用户关联"
        
        # 删除角色相关的权限记录
        cursor.execute("DELETE FROM knowledgebase_role WHERE role_id = %s", (role_id,))
        cursor.execute("DELETE FROM model_role WHERE role_id = %s", (role_id,))
        
        # 删除角色
        cursor.execute("DELETE FROM role WHERE id = %s", (role_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, None
        
    except mysql.connector.Error as err:
        print(f"删除角色错误: {err}")
        return False, str(err)


def set_default_role(role_id):
    """设置默认角色（取消其他默认角色）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 先取消所有默认角色
        cursor.execute("UPDATE role SET is_default = 0 WHERE is_default = 1")
        
        # 设置新的默认角色
        cursor.execute("UPDATE role SET is_default = 1 WHERE id = %s", (role_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"设置默认角色错误: {err}")
        return False


def unset_default_role(role_id):
    """取消默认角色"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE role SET is_default = 0 WHERE id = %s", (role_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"取消默认角色错误: {err}")
        return False


def get_role_users(role_id, current_page=1, page_size=10):
    """获取角色下的用户列表"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 查询总数
        count_sql = """
        SELECT COUNT(*) as total 
        FROM user_role ur 
        INNER JOIN user u ON ur.user_id = u.id 
        WHERE ur.role_id = %s
        """
        cursor.execute(count_sql, (role_id,))
        total = cursor.fetchone()['total']
        
        # 分页查询
        offset = (current_page - 1) * page_size
        query = """
        SELECT u.id, u.nickname, u.email, u.create_date
        FROM user_role ur
        INNER JOIN user u ON ur.user_id = u.id
        WHERE ur.role_id = %s
        ORDER BY u.nickname ASC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (role_id, page_size, offset))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        users = []
        for user in results:
            users.append({
                "id": user["id"],
                "username": user["nickname"],
                "email": user["email"],
                "createTime": user["create_date"].strftime("%Y-%m-%d %H:%M:%S") if user["create_date"] else "",
            })
        
        return users, total
        
    except mysql.connector.Error as err:
        print(f"获取角色用户错误: {err}")
        return [], 0


def get_user_roles(user_id):
    """获取用户的所有角色"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT r.id, r.name, r.is_default
        FROM user_role ur
        INNER JOIN role r ON ur.role_id = r.id
        WHERE ur.user_id = %s AND r.status = '1'
        ORDER BY r.name ASC
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [{"id": r["id"], "name": r["name"], "isDefault": r["is_default"] == 1} for r in results]
        
    except mysql.connector.Error as err:
        print(f"获取用户角色错误: {err}")
        return []


def get_user_effective_roles(user_id):
    """获取用户的有效角色（如果用户没有角色，返回默认角色）"""
    roles = get_user_roles(user_id)
    if roles:
        return roles
    
    # 返回默认角色
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT id, name, is_default
        FROM role
        WHERE is_default = 1 AND status = '1'
        LIMIT 1
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return [{"id": result["id"], "name": result["name"], "isDefault": True}]
        return []
        
    except mysql.connector.Error as err:
        print(f"获取默认角色错误: {err}")
        return []


def set_user_roles(user_id, role_ids):
    """设置用户的角色（多对多）"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取当前时间
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        target_tz = pytz.timezone('Asia/Shanghai')
        local_dt = utc_now.astimezone(target_tz)
        create_time = int(local_dt.timestamp() * 1000)
        current_date = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # 先删除用户的所有角色
        cursor.execute("DELETE FROM user_role WHERE user_id = %s", (user_id,))
        
        # 添加新的角色关联
        if role_ids:
            for role_id in role_ids:
                record_id = generate_uuid()
                cursor.execute("""
                    INSERT INTO user_role (id, user_id, role_id, create_time, create_date, update_time, update_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (record_id, user_id, role_id, create_time, current_date, create_time, current_date))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"设置用户角色错误: {err}")
        return False


def get_default_role():
    """获取默认角色"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, name FROM role WHERE is_default = 1 AND status = '1' LIMIT 1"
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result
        
    except mysql.connector.Error as err:
        print(f"获取默认角色错误: {err}")
        return None


# ===================== 知识库角色权限 =====================

def get_kb_roles(kb_id):
    """获取知识库的角色权限"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT r.id, r.name, r.is_default
        FROM knowledgebase_role kr
        INNER JOIN role r ON kr.role_id = r.id
        WHERE kr.kb_id = %s AND r.status = '1'
        ORDER BY r.name ASC
        """
        cursor.execute(query, (kb_id,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [{"id": r["id"], "name": r["name"], "isDefault": r["is_default"] == 1} for r in results]
        
    except mysql.connector.Error as err:
        print(f"获取知识库角色权限错误: {err}")
        return []


def set_kb_roles(kb_id, role_ids):
    """设置知识库的角色权限"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取当前时间
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        target_tz = pytz.timezone('Asia/Shanghai')
        local_dt = utc_now.astimezone(target_tz)
        create_time = int(local_dt.timestamp() * 1000)
        current_date = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # 先删除知识库的所有角色权限
        cursor.execute("DELETE FROM knowledgebase_role WHERE kb_id = %s", (kb_id,))
        
        # 添加新的角色权限
        if role_ids:
            for role_id in role_ids:
                record_id = generate_uuid()
                cursor.execute("""
                    INSERT INTO knowledgebase_role (id, kb_id, role_id, create_time, create_date, update_time, update_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (record_id, kb_id, role_id, create_time, current_date, create_time, current_date))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"设置知识库角色权限错误: {err}")
        return False


# ===================== 模型角色权限 =====================

def get_model_roles(tenant_id, llm_factory, llm_name):
    """获取模型的角色权限"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT r.id, r.name, r.is_default
        FROM model_role mr
        INNER JOIN role r ON mr.role_id = r.id
        WHERE mr.tenant_id = %s AND mr.llm_factory = %s AND mr.llm_name = %s AND r.status = '1'
        ORDER BY r.name ASC
        """
        cursor.execute(query, (tenant_id, llm_factory, llm_name))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return [{"id": r["id"], "name": r["name"], "isDefault": r["is_default"] == 1} for r in results]
        
    except mysql.connector.Error as err:
        print(f"获取模型角色权限错误: {err}")
        return []


def set_model_roles(tenant_id, llm_factory, llm_name, role_ids):
    """设置模型的角色权限"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 获取当前时间
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)
        target_tz = pytz.timezone('Asia/Shanghai')
        local_dt = utc_now.astimezone(target_tz)
        create_time = int(local_dt.timestamp() * 1000)
        current_date = local_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # 先删除模型的所有角色权限
        cursor.execute("""
            DELETE FROM model_role 
            WHERE tenant_id = %s AND llm_factory = %s AND llm_name = %s
        """, (tenant_id, llm_factory, llm_name))
        
        # 添加新的角色权限
        if role_ids:
            for role_id in role_ids:
                record_id = generate_uuid()
                cursor.execute("""
                    INSERT INTO model_role (id, tenant_id, llm_factory, llm_name, role_id, create_time, create_date, update_time, update_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (record_id, tenant_id, llm_factory, llm_name, role_id, create_time, current_date, create_time, current_date))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"设置模型角色权限错误: {err}")
        return False

