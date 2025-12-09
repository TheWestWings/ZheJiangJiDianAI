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
    get_llm_list
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
