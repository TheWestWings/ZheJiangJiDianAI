from flask import jsonify, request, g
from services.users.service import (
    get_users_with_pagination, delete_user, create_user, update_user, 
    reset_user_password, set_system_admin, is_super_admin, is_system_admin, 
    can_access_admin, SUPER_ADMIN_USER_ID
)
from middleware.permission import require_super_admin
from .. import users_bp

@users_bp.route('', methods=['GET'])
def get_users():
    """获取用户的API端点,支持分页和条件查询"""
    try:
        # 获取查询参数
        current_page = int(request.args.get('currentPage', 1))
        page_size = int(request.args.get('size', 10))
        username = request.args.get('username', '')
        email = request.args.get('email', '')
        sort_by = request.args.get("sort_by", "create_time")
        sort_order = request.args.get("sort_order", "desc")
        
        # 调用服务函数获取分页和筛选后的用户数据
        users, total = get_users_with_pagination(current_page, page_size, username, email, sort_by, sort_order)
        
        # 返回符合前端期望格式的数据
        return jsonify({
            "code": 0,  # 成功状态码
            "data": {
                "list": users,
                "total": total
            },
            "message": "获取用户列表成功"
        })
    except Exception as e:
        # 错误处理
        return jsonify({
            "code": 500,
            "message": f"获取用户列表失败: {str(e)}"
        }), 500

@users_bp.route('/<string:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    """删除用户的API端点"""
    delete_user(user_id)
    return jsonify({
        "code": 0,
        "message": f"用户 {user_id} 删除成功"
    })

@users_bp.route('', methods=['POST'])
def create_user_route():
    """创建用户的API端点"""
    data = request.json
    # 创建用户
    try:
        success = create_user(user_data=data)
        if success:
            return jsonify({
                "code": 0,
                "message": "用户创建成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": "用户创建失败"
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"用户创建失败: {str(e)}"
        }), 500

@users_bp.route('/<string:user_id>', methods=['PUT'])
def update_user_route(user_id):
    """更新用户的API端点"""
    data = request.json
    user_id = data.get('id')
    update_user(user_id=user_id, user_data=data)
    return jsonify({
        "code": 0,
        "message": f"用户 {user_id} 更新成功"
    })

@users_bp.route('/me', methods=['GET'])
def get_current_user():
    """获取当前登录用户信息"""
    # 从 g 对象获取已解析的用户信息
    current_user_id = getattr(g, 'user_id', None)
    is_super = getattr(g, 'is_super_admin', False)
    is_sys_admin = getattr(g, 'is_system_admin', False)
    username = getattr(g, 'username', 'admin')
    
    # 如果没有用户ID但有超管标识（.env 超管登录）
    if not current_user_id and is_super:
        return jsonify({
            "code": 0,
            "data": {
                "username": username,
                "roles": ["admin"],
                "is_super_admin": True,
                "is_system_admin": False
            },
            "message": "获取用户信息成功"
        })
    
    # 有用户ID的情况（数据库用户）
    if current_user_id:
        return jsonify({
            "code": 0,
            "data": {
                "user_id": current_user_id,
                "username": username,
                "roles": ["admin"],
                "is_super_admin": is_super,
                "is_system_admin": is_sys_admin,
                "can_access_admin": is_super or is_sys_admin
            },
            "message": "获取用户信息成功"
        })
    
    # 向后兼容：从 token 解析的超管
    return jsonify({
        "code": 0,
        "data": {
            "username": "admin",
            "roles": ["admin"],
            "is_super_admin": is_super,
            "is_system_admin": is_sys_admin
        },
        "message": "获取用户信息成功"
    })


@users_bp.route('/<string:user_id>/set-system-admin', methods=['POST'])
@require_super_admin
def set_system_admin_route(user_id):
    """设置用户为系统管理员（仅超级管理员可操作）"""
    try:
        success, message = set_system_admin(user_id, True)
        if success:
            return jsonify({
                "code": 0,
                "message": "设置系统管理员成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": message
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"设置系统管理员失败: {str(e)}"
        }), 500


@users_bp.route('/<string:user_id>/unset-system-admin', methods=['POST'])
@require_super_admin
def unset_system_admin_route(user_id):
    """取消用户的系统管理员身份（仅超级管理员可操作）"""
    try:
        success, message = set_system_admin(user_id, False)
        if success:
            return jsonify({
                "code": 0,
                "message": "取消系统管理员成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": message
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"取消系统管理员失败: {str(e)}"
        }), 500

@users_bp.route('/<string:user_id>/reset-password', methods=['PUT'])
def reset_password_route(user_id):
    """
    重置用户密码的API端点
    Args:
        user_id (str): 需要重置密码的用户ID
    Returns:
        Response: JSON响应
    """
    try:
        data = request.json
        new_password = data.get('password')

        # 校验密码是否存在
        if not new_password:
            return jsonify({"code": 400, "message": "缺少新密码参数 'password'"}), 400

        # 调用 service 函数重置密码
        success = reset_user_password(user_id=user_id, new_password=new_password)

        if success:
            return jsonify({
                "code": 0,
                "message": "用户密码重置成功"
            })
        else:
            # service 层可能因为用户不存在或其他原因返回 False
            return jsonify({"code": 404, "message": "用户未找到或密码重置失败"}), 404
    except Exception as e:
        # 统一处理异常
        return jsonify({
            "code": 500,
            "message": f"重置密码失败: {str(e)}"
        }), 500


@users_bp.route('/<string:user_id>/roles', methods=['GET'])
def get_user_roles_route(user_id):
    """获取用户的角色"""
    try:
        from services.roles.service import get_user_roles
        roles = get_user_roles(user_id)
        return jsonify({
            "code": 0,
            "data": roles,
            "message": "获取用户角色成功"
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取用户角色失败: {str(e)}"
        }), 500


@users_bp.route('/<string:user_id>/roles', methods=['PUT'])
def set_user_roles_route(user_id):
    """设置用户的角色"""
    try:
        from services.roles.service import set_user_roles
        data = request.json
        role_ids = data.get('role_ids', [])
        
        success = set_user_roles(user_id, role_ids)
        if success:
            return jsonify({
                "code": 0,
                "message": "设置用户角色成功"
            })
        else:
            return jsonify({
                "code": 400,
                "message": "设置用户角色失败"
            }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"设置用户角色失败: {str(e)}"
        }), 500


@users_bp.route('/batch', methods=['POST'])
def batch_create_users_route():
    """批量创建用户（通过Excel上传）"""
    try:
        import pandas as pd
        from io import BytesIO
        from services.users.service import create_user
        
        if 'file' not in request.files:
            return jsonify({"code": 400, "message": "未检测到文件"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"code": 400, "message": "未选择文件"}), 400
        
        # 检查文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"code": 400, "message": "请上传Excel文件（.xlsx或.xls）"}), 400
        
        # 读取Excel文件
        try:
            df = pd.read_excel(BytesIO(file.read()))
        except Exception as e:
            return jsonify({"code": 400, "message": f"Excel文件读取失败: {str(e)}"}), 400
        
        # 检查必要列是否存在
        required_columns = ['username', 'email', 'password']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                "code": 400, 
                "message": f"Excel缺少必要列: {', '.join(missing_columns)}"
            }), 400
        
        # 批量创建用户
        success_count = 0
        failed_users = []
        
        for index, row in df.iterrows():
            try:
                username = str(row['username']).strip()
                email = str(row['email']).strip()
                password = str(row['password']).strip()
                
                # 跳过空行
                if not username or not email or not password or username == 'nan':
                    continue
                
                user_data = {
                    "username": username,
                    "email": email,
                    "password": password
                }
                
                result = create_user(user_data)
                if result:
                    success_count += 1
                else:
                    failed_users.append({"row": index + 2, "email": email, "reason": "创建失败"})
            except Exception as e:
                failed_users.append({
                    "row": index + 2, 
                    "email": str(row.get('email', 'unknown')), 
                    "reason": str(e)
                })
        
        message = f"成功创建 {success_count} 个用户"
        if failed_users:
            message += f"，{len(failed_users)} 个用户创建失败"
        
        return jsonify({
            "code": 0,
            "data": {
                "success_count": success_count,
                "failed_count": len(failed_users),
                "failed_users": failed_users
            },
            "message": message
        })
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"批量创建用户失败: {str(e)}"
        }), 500


@users_bp.route('/template', methods=['GET'])
def download_user_template():
    """下载用户导入模板"""
    try:
        import pandas as pd
        from io import BytesIO
        from flask import send_file
        
        # 创建模板数据（只包含表头，不包含示例数据）
        template_data = {
            'username': [],
            'email': [],
            'password': []
        }
        
        df = pd.DataFrame(template_data)
        
        # 导出到内存中的Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='用户数据')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='user_import_template.xlsx'
        )
        
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"生成模板失败: {str(e)}"
        }), 500