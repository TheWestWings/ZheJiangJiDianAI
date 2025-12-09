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
