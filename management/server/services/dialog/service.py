"""
助理(Dialog)管理服务
提供助理的增删改查和默认助理设置功能
"""
from database import get_db_connection, get_redis_connection
import json
from datetime import datetime
import uuid
import time


def get_dialog_list(page=1, size=20, name=None, tenant_id=None):
    """
    获取助理列表
    :param page: 页码
    :param size: 每页数量
    :param name: 助理名称（模糊搜索）
    :param tenant_id: 租户ID（可选，用于过滤特定用户的助理）
    :return: 助理列表和总数
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 构建查询条件
        where_clauses = ["status = '1'"]  # 只查询有效的助理
        params = []
        
        if name:
            where_clauses.append("name LIKE %s")
            params.append(f"%{name}%")
        
        if tenant_id:
            where_clauses.append("tenant_id = %s")
            params.append(tenant_id)
        
        where_sql = " AND ".join(where_clauses)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM dialog WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']
        
        # 查询列表
        offset = (page - 1) * size
        list_sql = f"""
            SELECT id, name, description, icon, tenant_id, 
                   llm_id, kb_ids, create_time, update_time
            FROM dialog 
            WHERE {where_sql}
            ORDER BY create_time DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(list_sql, params + [size, offset])
        dialogs = cursor.fetchall()
        
        # 处理日期时间序列化
        for dialog in dialogs:
            if dialog.get('create_time'):
                ct = dialog['create_time']
                if isinstance(ct, int):
                    dialog['create_time'] = datetime.fromtimestamp(ct / 1000).isoformat() if ct > 1e12 else datetime.fromtimestamp(ct).isoformat()
                elif hasattr(ct, 'isoformat'):
                    dialog['create_time'] = ct.isoformat()
                else:
                    dialog['create_time'] = str(ct)
            if dialog.get('update_time'):
                ut = dialog['update_time']
                if isinstance(ut, int):
                    dialog['update_time'] = datetime.fromtimestamp(ut / 1000).isoformat() if ut > 1e12 else datetime.fromtimestamp(ut).isoformat()
                elif hasattr(ut, 'isoformat'):
                    dialog['update_time'] = ut.isoformat()
                else:
                    dialog['update_time'] = str(ut)
            # 解析 kb_ids JSON
            if dialog.get('kb_ids'):
                try:
                    dialog['kb_ids'] = json.loads(dialog['kb_ids'])
                except:
                    dialog['kb_ids'] = []
        
        return {
            'list': dialogs,
            'total': total,
            'page': page,
            'size': size
        }
    finally:
        cursor.close()
        conn.close()


def get_dialog_by_id(dialog_id):
    """
    根据ID获取助理详情
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql = """
            SELECT id, name, description, icon, tenant_id,
                   llm_id, llm_setting, prompt_config, kb_ids,
                   top_n, top_k, rerank_id, similarity_threshold,
                   vector_similarity_weight, create_time, update_time
            FROM dialog 
            WHERE id = %s AND status = '1'
        """
        cursor.execute(sql, (dialog_id,))
        dialog = cursor.fetchone()
        
        if dialog:
            if dialog.get('create_time'):
                ct = dialog['create_time']
                if isinstance(ct, int):
                    dialog['create_time'] = datetime.fromtimestamp(ct / 1000).isoformat() if ct > 1e12 else datetime.fromtimestamp(ct).isoformat()
                elif hasattr(ct, 'isoformat'):
                    dialog['create_time'] = ct.isoformat()
                else:
                    dialog['create_time'] = str(ct)
            if dialog.get('update_time'):
                ut = dialog['update_time']
                if isinstance(ut, int):
                    dialog['update_time'] = datetime.fromtimestamp(ut / 1000).isoformat() if ut > 1e12 else datetime.fromtimestamp(ut).isoformat()
                elif hasattr(ut, 'isoformat'):
                    dialog['update_time'] = ut.isoformat()
                else:
                    dialog['update_time'] = str(ut)
            if dialog.get('kb_ids'):
                try:
                    dialog['kb_ids'] = json.loads(dialog['kb_ids'])
                except:
                    dialog['kb_ids'] = []
            if dialog.get('llm_setting'):
                try:
                    dialog['llm_setting'] = json.loads(dialog['llm_setting'])
                except:
                    dialog['llm_setting'] = {}
            if dialog.get('prompt_config'):
                try:
                    dialog['prompt_config'] = json.loads(dialog['prompt_config'])
                except:
                    dialog['prompt_config'] = {}
        
        return dialog
    finally:
        cursor.close()
        conn.close()


def create_dialog(data, tenant_id):
    """
    创建新助理
    :param data: 助理数据
    :param tenant_id: 租户ID（助理所属用户）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        dialog_id = str(uuid.uuid4()).replace('-', '')
        now = int(time.time() * 1000)  # 毫秒时间戳
        
        # 默认提示词配置
        default_prompt = {
            "system": """你是一个智能助手，请总结知识库的内容来回答问题，请列举知识库中的数据详细回答。当所有知识库内容都与问题无关时，你的回答必须包括"知识库中未找到您要的答案！"这句话。回答需要考虑聊天历史。
以下是知识库：
{knowledge}
以上是知识库。""",
            "prologue": "您好，我是您的助手，有什么可以帮您？",
            "parameters": [{"key": "knowledge", "optional": False}],
            "empty_response": "抱歉，知识库中未找到相关内容！"
        }
        
        sql = """
            INSERT INTO dialog (
                id, tenant_id, name, description, icon,
                llm_id, llm_setting, prompt_config, kb_ids,
                top_n, top_k, rerank_id, similarity_threshold,
                vector_similarity_weight, prompt_type, do_refer, status, create_time, update_time
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            dialog_id,
            tenant_id,
            data.get('name', '新助理'),
            data.get('description', ''),
            data.get('icon', ''),
            data.get('llm_id', ''),
            json.dumps(data.get('llm_setting', {})),
            json.dumps(data.get('prompt_config', default_prompt)),
            json.dumps(data.get('kb_ids', [])),
            data.get('top_n', 6),
            data.get('top_k', 1024),
            data.get('rerank_id', ''),
            data.get('similarity_threshold', 0.1),
            data.get('vector_similarity_weight', 0.3),
            'simple',  # prompt_type
            '1',  # do_refer
            '1',  # status
            now,
            now
        )
        
        cursor.execute(sql, params)
        conn.commit()
        
        return {'id': dialog_id, 'success': True}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def update_dialog(dialog_id, data):
    """
    更新助理信息
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 构建更新字段
        update_fields = []
        params = []
        
        field_mapping = {
            'name': 'name',
            'description': 'description',
            'icon': 'icon',
            'llm_id': 'llm_id',
            'top_n': 'top_n',
            'top_k': 'top_k',
            'rerank_id': 'rerank_id',
            'similarity_threshold': 'similarity_threshold',
            'vector_similarity_weight': 'vector_similarity_weight',
        }
        
        for key, field in field_mapping.items():
            if key in data:
                update_fields.append(f"{field} = %s")
                params.append(data[key])
        
        # JSON 字段特殊处理
        if 'kb_ids' in data:
            update_fields.append("kb_ids = %s")
            params.append(json.dumps(data['kb_ids']))
        
        if 'llm_setting' in data:
            update_fields.append("llm_setting = %s")
            params.append(json.dumps(data['llm_setting']))
        
        if 'prompt_config' in data:
            update_fields.append("prompt_config = %s")
            params.append(json.dumps(data['prompt_config']))
        
        if not update_fields:
            return {'success': False, 'message': '没有要更新的字段'}
        
        update_fields.append("update_time = %s")
        params.append(int(time.time() * 1000))
        params.append(dialog_id)
        
        sql = f"UPDATE dialog SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, params)
        conn.commit()
        
        return {'success': True}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def delete_dialog(dialog_id):
    """
    删除助理（软删除）
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        sql = "UPDATE dialog SET status = '0', update_time = %s WHERE id = %s"
        cursor.execute(sql, (int(time.time() * 1000), dialog_id))
        conn.commit()
        return {'success': True}
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def set_default_dialog(dialog_id):
    """
    设置默认助理（存储在 Redis 中）
    """
    try:
        redis_conn = get_redis_connection()
        redis_conn.set('system:default_dialog_id', dialog_id)
        return {'success': True}
    except Exception as e:
        raise e


def get_default_dialog():
    """
    获取默认助理ID
    """
    try:
        redis_conn = get_redis_connection()
        dialog_id = redis_conn.get('system:default_dialog_id')
        if dialog_id:
            return dialog_id.decode('utf-8')
        return None
    except Exception as e:
        raise e


def get_tenant_list():
    """
    获取所有租户列表（用于选择助理所属用户）
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql = """
            SELECT t.id, u.nickname, u.email
            FROM tenant t
            LEFT JOIN user u ON t.id = u.id
            WHERE t.status = '1'
            ORDER BY t.create_time DESC
            LIMIT 100
        """
        cursor.execute(sql)
        tenants = cursor.fetchall()
        return tenants
    finally:
        cursor.close()
        conn.close()


def get_knowledgebase_list():
    """
    获取所有知识库列表（用于选择助理关联的知识库）
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql = """
            SELECT id, name, description, tenant_id
            FROM knowledgebase
            WHERE status = '1'
            ORDER BY create_time DESC
            LIMIT 200
        """
        cursor.execute(sql)
        knowledgebases = cursor.fetchall()
        return knowledgebases
    finally:
        cursor.close()
        conn.close()


def get_llm_list():
    """
    获取所有可用的LLM模型列表
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 从 tenant_llm 表获取已配置的模型
        sql = """
            SELECT DISTINCT llm_name, model_type, llm_factory as fid
            FROM tenant_llm
            WHERE model_type = 'chat'
            ORDER BY llm_name
        """
        cursor.execute(sql)
        llms = cursor.fetchall()
        return llms
    finally:
        cursor.close()
        conn.close()


def get_all_models_with_status():
    """
    获取所有已配置的模型及其全局启用状态
    用于后台管理页面展示
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql = """
            SELECT DISTINCT 
                llm_name, 
                llm_factory, 
                model_type,
                api_base,
                MAX(global_enabled) as global_enabled
            FROM tenant_llm
            WHERE model_type = 'chat'
            GROUP BY llm_name, llm_factory, model_type, api_base
            ORDER BY llm_factory, llm_name
        """
        cursor.execute(sql)
        models = cursor.fetchall()
        
        # 转换 global_enabled 为布尔值
        for model in models:
            model['global_enabled'] = bool(model.get('global_enabled', 0))
        
        return models
    finally:
        cursor.close()
        conn.close()


def set_model_global_enabled(llm_name, llm_factory, enabled):
    """
    设置模型的全局启用状态
    :param llm_name: 模型名称
    :param llm_factory: 模型厂商
    :param enabled: 是否启用 (True/False)
    :return: 影响的行数
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        enabled_value = 1 if enabled else 0
        sql = """
            UPDATE tenant_llm 
            SET global_enabled = %s 
            WHERE llm_name = %s AND llm_factory = %s
        """
        cursor.execute(sql, (enabled_value, llm_name, llm_factory))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def get_globally_enabled_models():
    """
    获取所有全局启用的模型
    用于前台展示可选模型
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        sql = """
            SELECT DISTINCT 
                llm_name, 
                llm_factory, 
                model_type
            FROM tenant_llm
            WHERE model_type = 'chat' AND global_enabled = 1
            ORDER BY llm_factory, llm_name
        """
        cursor.execute(sql)
        models = cursor.fetchall()
        return models
    finally:
        cursor.close()
        conn.close()


def create_model(llm_name, llm_factory, model_type, api_base, api_key, global_enabled=True):
    """
    创建新模型
    :param llm_name: 模型名称
    :param llm_factory: 模型厂商
    :param model_type: 模型类型
    :param api_base: API Base URL
    :param api_key: API Key
    :param global_enabled: 是否全局启用
    :return: 是否成功
    """
    import uuid
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查是否已存在相同的模型
        check_sql = """
            SELECT COUNT(*) as count FROM tenant_llm 
            WHERE llm_name = %s AND llm_factory = %s
        """
        cursor.execute(check_sql, (llm_name, llm_factory))
        result = cursor.fetchone()
        if result and result[0] > 0:
            raise ValueError(f"模型 {llm_name} ({llm_factory}) 已存在")
        
        # 获取系统租户 ID (使用 admin 用户的 ID)
        tenant_sql = "SELECT id FROM user WHERE email = 'admin@admin.com' OR nickname = 'admin' LIMIT 1"
        cursor.execute(tenant_sql)
        tenant_row = cursor.fetchone()
        if tenant_row:
            tenant_id = tenant_row[0]
        else:
            tenant_id = str(uuid.uuid4()).replace('-', '')
        
        # 插入模型
        # create_time/update_time 是 bigint 毫秒时间戳
        # create_date/update_date 是 datetime 字符串
        now_timestamp = int(time.time() * 1000)  # 毫秒时间戳
        now_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # datetime字符串
        enabled_value = 1 if global_enabled else 0
        
        insert_sql = """
            INSERT INTO tenant_llm 
            (create_time, create_date, update_time, update_date, tenant_id, llm_factory, model_type, llm_name, api_key, api_base, max_tokens, used_tokens, global_enabled)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            now_timestamp, now_datetime, now_timestamp, now_datetime,
            tenant_id, llm_factory, model_type, llm_name, api_key, api_base,
            8192, 0, enabled_value
        ))
        conn.commit()
        return True
    finally:
        cursor.close()
        conn.close()


def update_model(llm_name, llm_factory, api_base=None, api_key=None, global_enabled=None):
    """
    更新模型信息
    :param llm_name: 模型名称
    :param llm_factory: 模型厂商
    :param api_base: API Base URL (可选)
    :param api_key: API Key (可选)
    :param global_enabled: 是否全局启用 (可选)
    :return: 影响的行数
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 动态构建更新语句
        updates = []
        params = []
        
        now_timestamp = int(time.time() * 1000)  # 毫秒时间戳
        now_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # datetime字符串
        updates.append("update_time = %s")
        params.append(now_timestamp)
        updates.append("update_date = %s")
        params.append(now_datetime)
        
        if api_base is not None:
            updates.append("api_base = %s")
            params.append(api_base)
        
        if api_key is not None and api_key.strip():
            updates.append("api_key = %s")
            params.append(api_key)
        
        if global_enabled is not None:
            updates.append("global_enabled = %s")
            params.append(1 if global_enabled else 0)
        
        if not updates:
            return 0
        
        params.extend([llm_name, llm_factory])
        sql = f"""
            UPDATE tenant_llm 
            SET {', '.join(updates)}
            WHERE llm_name = %s AND llm_factory = %s
        """
        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def delete_model(llm_name, llm_factory):
    """
    删除模型
    :param llm_name: 模型名称
    :param llm_factory: 模型厂商
    :return: 影响的行数
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        sql = """
            DELETE FROM tenant_llm 
            WHERE llm_name = %s AND llm_factory = %s
        """
        cursor.execute(sql, (llm_name, llm_factory))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()

