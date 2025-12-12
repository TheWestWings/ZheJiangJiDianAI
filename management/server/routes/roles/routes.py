"""
角色管理路由

提供角色的CRUD操作、默认角色设置、角色用户查看等API
"""
from flask import jsonify, request
from services.roles.service import (
    get_roles_with_pagination,
    get_all_roles,
    create_role,
    update_role,
    delete_role,
    set_default_role,
    unset_default_role,
    get_role_users
)
from .. import roles_bp


@roles_bp.route('', methods=['GET'])
def get_roles():
    """获取角色列表（分页）"""
    try:
        current_page = int(request.args.get('currentPage', 1))
        page_size = int(request.args.get('size', 10))
        name = request.args.get('name', '')
        sort_by = request.args.get('sort_by', 'create_time')
        sort_order = request.args.get('sort_order', 'desc')
        
        roles, total = get_roles_with_pagination(current_page, page_size, name, sort_by, sort_order)
        
        return jsonify({
            "code": 0,
            "data": {
                "list": roles,
                "total": total
            },
            "message": "获取角色列表成功"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取角色列表失败: {str(e)}"
        }), 500


@roles_bp.route('/all', methods=['GET'])
def get_all_roles_route():
    """获取所有启用的角色（用于下拉选择）"""
    try:
        roles = get_all_roles()
        return jsonify({
            "code": 0,
            "data": roles,
            "message": "获取角色列表成功"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取角色列表失败: {str(e)}"
        }), 500


@roles_bp.route('', methods=['POST'])
def create_role_route():
    """创建角色"""
    try:
        data = request.json
        if not data or not data.get('name'):
            return jsonify({
                "code": 400,
                "message": "角色名称不能为空"
            }), 400
        
        success, result = create_role(data)
        if success:
            return jsonify({
                "code": 0,
                "data": {"id": result},
                "message": "角色创建成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": f"角色创建失败: {result}"
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"角色创建失败: {str(e)}"
        }), 500


@roles_bp.route('/<string:role_id>', methods=['PUT'])
def update_role_route(role_id):
    """更新角色"""
    try:
        data = request.json
        success = update_role(role_id, data)
        if success:
            return jsonify({
                "code": 0,
                "message": "角色更新成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": "角色更新失败"
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"角色更新失败: {str(e)}"
        }), 500


@roles_bp.route('/<string:role_id>', methods=['DELETE'])
def delete_role_route(role_id):
    """删除角色"""
    try:
        success, error = delete_role(role_id)
        if success:
            return jsonify({
                "code": 0,
                "message": "角色删除成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": error or "角色删除失败"
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"角色删除失败: {str(e)}"
        }), 500


@roles_bp.route('/<string:role_id>/set-default', methods=['POST'])
def set_default_role_route(role_id):
    """设置为默认角色"""
    try:
        success = set_default_role(role_id)
        if success:
            return jsonify({
                "code": 0,
                "message": "设置默认角色成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": "设置默认角色失败"
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"设置默认角色失败: {str(e)}"
        }), 500


@roles_bp.route('/<string:role_id>/unset-default', methods=['POST'])
def unset_default_role_route(role_id):
    """取消默认角色"""
    try:
        success = unset_default_role(role_id)
        if success:
            return jsonify({
                "code": 0,
                "message": "取消默认角色成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": "取消默认角色失败"
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"取消默认角色失败: {str(e)}"
        }), 500


@roles_bp.route('/<string:role_id>/users', methods=['GET'])
def get_role_users_route(role_id):
    """获取角色下的用户列表"""
    try:
        current_page = int(request.args.get('currentPage', 1))
        page_size = int(request.args.get('size', 10))
        
        users, total = get_role_users(role_id, current_page, page_size)
        
        return jsonify({
            "code": 0,
            "data": {
                "list": users,
                "total": total
            },
            "message": "获取角色用户列表成功"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取角色用户列表失败: {str(e)}"
        }), 500
