"""
助理管理路由
"""
from flask import request, jsonify
from routes import dialog_bp
from services.dialog.service import (
    get_dialog_list,
    get_dialog_by_id,
    create_dialog,
    update_dialog,
    delete_dialog,
    set_default_dialog,
    get_default_dialog,
    get_tenant_list,
    get_knowledgebase_list,
    get_llm_list,
    get_all_models_with_status,
    set_model_global_enabled,
    get_globally_enabled_models,
    create_model,
    update_model,
    delete_model
)


@dialog_bp.route('', methods=['GET'])
def list_dialogs():
    """获取助理列表"""
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        name = request.args.get('name', None)
        tenant_id = request.args.get('tenant_id', None)
        
        result = get_dialog_list(page=page, size=size, name=name, tenant_id=tenant_id)
        return jsonify({'code': 0, 'data': result, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/<dialog_id>', methods=['GET'])
def get_dialog(dialog_id):
    """获取助理详情"""
    try:
        dialog = get_dialog_by_id(dialog_id)
        if dialog:
            return jsonify({'code': 0, 'data': dialog, 'message': 'success'})
        else:
            return jsonify({'code': 404, 'message': '助理不存在'}), 404
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('', methods=['POST'])
def add_dialog():
    """创建新助理"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        tenant_id = data.get('tenant_id')
        if not tenant_id:
            return jsonify({'code': 400, 'message': '请选择助理所属用户'}), 400
        
        result = create_dialog(data, tenant_id)
        return jsonify({'code': 0, 'data': result, 'message': '创建成功'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/<dialog_id>', methods=['PUT'])
def modify_dialog(dialog_id):
    """更新助理信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        result = update_dialog(dialog_id, data)
        return jsonify({'code': 0, 'data': result, 'message': '更新成功'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/<dialog_id>', methods=['DELETE'])
def remove_dialog(dialog_id):
    """删除助理"""
    try:
        result = delete_dialog(dialog_id)
        return jsonify({'code': 0, 'data': result, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/<dialog_id>/set-default', methods=['POST'])
def set_default(dialog_id):
    """设置默认助理"""
    try:
        result = set_default_dialog(dialog_id)
        return jsonify({'code': 0, 'data': result, 'message': '设置成功'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/default', methods=['GET'])
def get_default():
    """获取默认助理ID"""
    try:
        dialog_id = get_default_dialog()
        return jsonify({'code': 0, 'data': {'dialog_id': dialog_id}, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/tenants', methods=['GET'])
def list_tenants():
    """获取租户列表（用于选择助理所属用户）"""
    try:
        tenants = get_tenant_list()
        return jsonify({'code': 0, 'data': tenants, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/knowledgebases', methods=['GET'])
def list_knowledgebases():
    """获取知识库列表（用于选择助理关联的知识库）"""
    try:
        knowledgebases = get_knowledgebase_list()
        return jsonify({'code': 0, 'data': knowledgebases, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/llms', methods=['GET'])
def list_llms():
    """获取可用的LLM模型列表"""
    try:
        llms = get_llm_list()
        return jsonify({'code': 0, 'data': llms, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/models', methods=['GET'])
def list_models_with_status():
    """获取所有模型及其启用状态（用于后台管理）"""
    try:
        models = get_all_models_with_status()
        return jsonify({'code': 0, 'data': models, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/model/enable', methods=['POST'])
def enable_model():
    """启用模型（全局）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        llm_name = data.get('llm_name')
        llm_factory = data.get('llm_factory')
        
        if not llm_name or not llm_factory:
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
        affected_rows = set_model_global_enabled(llm_name, llm_factory, True)
        return jsonify({
            'code': 0, 
            'data': {'affected_rows': affected_rows}, 
            'message': '模型已启用'
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/model/disable', methods=['POST'])
def disable_model():
    """禁用模型（全局）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        llm_name = data.get('llm_name')
        llm_factory = data.get('llm_factory')
        
        if not llm_name or not llm_factory:
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
        affected_rows = set_model_global_enabled(llm_name, llm_factory, False)
        return jsonify({
            'code': 0, 
            'data': {'affected_rows': affected_rows}, 
            'message': '模型已禁用'
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/models/enabled', methods=['GET'])
def list_enabled_models():
    """获取所有已启用的模型（用于前台）"""
    try:
        models = get_globally_enabled_models()
        return jsonify({'code': 0, 'data': models, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/model/create', methods=['POST'])
def create_model_route():
    """创建新模型"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        llm_name = data.get('llm_name')
        llm_factory = data.get('llm_factory')
        model_type = data.get('model_type', 'chat')
        api_base = data.get('api_base')
        api_key = data.get('api_key')
        global_enabled = data.get('global_enabled', True)
        
        if not llm_name or not llm_factory or not api_base or not api_key:
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
        create_model(llm_name, llm_factory, model_type, api_base, api_key, global_enabled)
        return jsonify({
            'code': 0, 
            'message': '模型创建成功'
        })
    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/model/update', methods=['POST'])
def update_model_route():
    """更新模型信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        llm_name = data.get('llm_name')
        llm_factory = data.get('llm_factory')
        
        if not llm_name or not llm_factory:
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
        api_base = data.get('api_base')
        api_key = data.get('api_key')
        global_enabled = data.get('global_enabled')
        
        affected_rows = update_model(llm_name, llm_factory, api_base, api_key, global_enabled)
        return jsonify({
            'code': 0, 
            'data': {'affected_rows': affected_rows}, 
            'message': '模型更新成功'
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/model/delete', methods=['POST'])
def delete_model_route():
    """删除模型"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400
        
        llm_name = data.get('llm_name')
        llm_factory = data.get('llm_factory')
        
        if not llm_name or not llm_factory:
            return jsonify({'code': 400, 'message': '缺少必要参数'}), 400
        
        affected_rows = delete_model(llm_name, llm_factory)
        if affected_rows == 0:
            return jsonify({'code': 404, 'message': '模型不存在'}), 404
        
        return jsonify({
            'code': 0, 
            'data': {'affected_rows': affected_rows}, 
            'message': '模型删除成功'
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


# ===================== 模型角色权限 =====================

@dialog_bp.route('/model/<string:llm_factory>/<string:llm_name>/roles', methods=['GET'])
def get_model_roles_route(llm_factory, llm_name):
    """获取模型的角色权限"""
    try:
        from services.roles.service import get_model_roles
        # 这里使用一个统一的 tenant_id（可以是第一个租户或者系统配置）
        from database import DB_CONFIG
        import mysql.connector
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM tenant LIMIT 1")
        tenant = cursor.fetchone()
        cursor.close()
        conn.close()
        
        tenant_id = tenant['id'] if tenant else 'system'
        roles = get_model_roles(tenant_id, llm_factory, llm_name)
        return jsonify({'code': 0, 'data': roles, 'message': 'success'})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@dialog_bp.route('/model/<string:llm_factory>/<string:llm_name>/roles', methods=['PUT'])
def set_model_roles_route(llm_factory, llm_name):
    """设置模型的角色权限"""
    try:
        from services.roles.service import set_model_roles
        from database import DB_CONFIG
        import mysql.connector
        
        data = request.get_json()
        role_ids = data.get('role_ids', [])
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM tenant LIMIT 1")
        tenant = cursor.fetchone()
        cursor.close()
        conn.close()
        
        tenant_id = tenant['id'] if tenant else 'system'
        success = set_model_roles(tenant_id, llm_factory, llm_name, role_ids)
        
        if success:
            return jsonify({'code': 0, 'message': '设置模型角色权限成功'})
        else:
            return jsonify({'code': 400, 'message': '设置模型角色权限失败'}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
