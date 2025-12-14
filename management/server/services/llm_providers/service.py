# LLM Providers 服务层
import json
import os
import sys

# 添加主项目路径以导入 rag 模块
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))))

from database import get_db_connection


# 系统租户ID，用于管理员统一配置
SYSTEM_TENANT_ID = os.getenv("SYSTEM_TENANT_ID", "system_admin")


def get_llm_factories_from_json():
    """从配置文件获取所有LLM工厂列表"""
    try:
        conf_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
            "conf", "llm_factories.json"
        )
        with open(conf_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("factory_llm_infos", [])
    except Exception as e:
        print(f"读取llm_factories.json失败: {e}")
        return []


def get_factories():
    """获取所有可用的模型工厂列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 从数据库获取工厂信息
        cursor.execute("""
            SELECT name, logo, tags, status 
            FROM llm_factories 
            WHERE name NOT IN ('Youdao', 'FastEmbed', 'BAAI')
            AND status = '1'
        """)
        factories = cursor.fetchall()
        
        # 获取每个工厂支持的模型类型
        cursor.execute("""
            SELECT fid, GROUP_CONCAT(DISTINCT model_type) as model_types
            FROM llm
            WHERE status = '1'
            GROUP BY fid
        """)
        model_types_map = {row['fid']: row['model_types'].split(',') if row['model_types'] else [] 
                          for row in cursor.fetchall()}
        
        for factory in factories:
            factory['model_types'] = model_types_map.get(factory['name'], 
                ['chat', 'embedding', 'rerank', 'image2text', 'speech2text', 'tts'])
        
        cursor.close()
        conn.close()
        return factories
    except Exception as e:
        print(f"获取工厂列表失败: {e}")
        return []


def get_my_llms(tenant_id=None):
    """获取已配置的模型列表"""
    if tenant_id is None:
        tenant_id = SYSTEM_TENANT_ID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                t.llm_factory, 
                f.logo, 
                f.tags, 
                t.model_type, 
                t.llm_name, 
                t.used_tokens
            FROM tenant_llm t
            LEFT JOIN llm_factories f ON t.llm_factory = f.name
            WHERE t.tenant_id = %s AND t.api_key IS NOT NULL AND t.api_key != ''
        """, (tenant_id,))
        
        llms = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # 按工厂分组
        result = {}
        for llm in llms:
            factory = llm['llm_factory']
            if factory not in result:
                result[factory] = {
                    'tags': llm['tags'] or '',
                    'llm': []
                }
            result[factory]['llm'].append({
                'type': llm['model_type'],
                'name': llm['llm_name'],
                'used_token': llm['used_tokens'] or 0
            })
        
        return result
    except Exception as e:
        print(f"获取已配置模型失败: {e}")
        return {}


def get_models_by_factory(factory_name):
    """获取指定工厂的所有预定义模型"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT llm_name, model_type, max_tokens, tags
            FROM llm
            WHERE fid = %s AND status = '1'
        """, (factory_name,))
        
        models = cursor.fetchall()
        cursor.close()
        conn.close()
        return models
    except Exception as e:
        print(f"获取工厂模型失败: {e}")
        return []


def set_api_key(factory, api_key, base_url="", tenant_id=None):
    """
    设置API Key，批量导入该工厂下的所有模型
    对应前台的set_api_key功能
    """
    if tenant_id is None:
        tenant_id = SYSTEM_TENANT_ID
    
    try:
        # 获取该工厂下的所有预定义模型
        models = get_models_by_factory(factory)
        if not models:
            return False, f"未找到工厂 {factory} 的模型定义"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for model in models:
            # 尝试更新，如果不存在则插入
            cursor.execute("""
                INSERT INTO tenant_llm (tenant_id, llm_factory, llm_name, model_type, api_key, api_base, max_tokens, used_tokens)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    api_key = VALUES(api_key),
                    api_base = VALUES(api_base),
                    max_tokens = VALUES(max_tokens)
            """, (
                tenant_id, 
                factory, 
                model['llm_name'], 
                model['model_type'], 
                api_key, 
                base_url, 
                model['max_tokens'],
                0
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, f"成功导入 {len(models)} 个模型"
    except Exception as e:
        print(f"设置API Key失败: {e}")
        return False, str(e)


def add_llm(llm_factory, llm_name, model_type, api_key, api_base="", max_tokens=4096, tenant_id=None):
    """
    添加单个自定义模型
    对应前台的add_llm功能
    """
    if tenant_id is None:
        tenant_id = SYSTEM_TENANT_ID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tenant_llm (tenant_id, llm_factory, llm_name, model_type, api_key, api_base, max_tokens, used_tokens)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                api_key = VALUES(api_key),
                api_base = VALUES(api_base),
                max_tokens = VALUES(max_tokens),
                model_type = VALUES(model_type)
        """, (tenant_id, llm_factory, llm_name, model_type, api_key, api_base, max_tokens, 0))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "模型添加成功"
    except Exception as e:
        print(f"添加模型失败: {e}")
        return False, str(e)


def delete_llm(llm_factory, llm_name, tenant_id=None):
    """删除单个模型"""
    if tenant_id is None:
        tenant_id = SYSTEM_TENANT_ID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM tenant_llm
            WHERE tenant_id = %s AND llm_factory = %s AND llm_name = %s
        """, (tenant_id, llm_factory, llm_name))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, "模型删除成功"
    except Exception as e:
        print(f"删除模型失败: {e}")
        return False, str(e)


def delete_factory(llm_factory, tenant_id=None):
    """删除整个工厂的所有模型配置"""
    if tenant_id is None:
        tenant_id = SYSTEM_TENANT_ID
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM tenant_llm
            WHERE tenant_id = %s AND llm_factory = %s
        """, (tenant_id, llm_factory))
        
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return True, f"已删除 {affected} 个模型配置"
    except Exception as e:
        print(f"删除工厂配置失败: {e}")
        return False, str(e)


def list_llms(model_type=None, tenant_id=None):
    """
    获取模型列表，包含可用性状态
    对应前台的list功能
    """
    if tenant_id is None:
        tenant_id = SYSTEM_TENANT_ID
    
    self_deployed = ["Youdao", "FastEmbed", "BAAI", "Ollama", "Xinference", "LocalAI", "LM-Studio", "GPUStack"]
    weighted = ["Youdao", "FastEmbed", "BAAI"]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取用户已配置的工厂
        cursor.execute("""
            SELECT DISTINCT llm_factory 
            FROM tenant_llm 
            WHERE tenant_id = %s AND api_key IS NOT NULL AND api_key != ''
        """, (tenant_id,))
        configured_factories = set(row['llm_factory'] for row in cursor.fetchall())
        
        # 获取所有可用模型
        query = """
            SELECT llm_name, model_type, fid, max_tokens, tags
            FROM llm
            WHERE status = '1' AND fid NOT IN ('Youdao', 'FastEmbed', 'BAAI')
        """
        if model_type:
            query += f" AND model_type LIKE '%{model_type}%'"
        
        cursor.execute(query)
        llms = cursor.fetchall()
        
        # 添加可用性标记
        for llm in llms:
            llm['available'] = (
                llm['fid'] in configured_factories or 
                llm['llm_name'].lower() == 'flag-embedding' or 
                llm['fid'] in self_deployed
            )
        
        # 获取用户自定义模型
        llm_set = set(f"{m['llm_name']}@{m['fid']}" for m in llms)
        
        cursor.execute("""
            SELECT llm_name, model_type, llm_factory as fid
            FROM tenant_llm
            WHERE tenant_id = %s AND api_key IS NOT NULL AND api_key != ''
        """, (tenant_id,))
        
        for row in cursor.fetchall():
            if f"{row['llm_name']}@{row['fid']}" not in llm_set:
                llms.append({
                    'llm_name': row['llm_name'],
                    'model_type': row['model_type'],
                    'fid': row['fid'],
                    'available': True
                })
        
        cursor.close()
        conn.close()
        
        # 按工厂分组
        result = {}
        for m in llms:
            if model_type and model_type not in m.get('model_type', ''):
                continue
            fid = m['fid']
            if fid not in result:
                result[fid] = []
            result[fid].append(m)
        
        return result
    except Exception as e:
        print(f"获取模型列表失败: {e}")
        return {}
