"""
权限验证中间件
提供装饰器用于保护需要特定权限的 API 端点
"""
import os
from functools import wraps
from flask import request, jsonify, g
import jwt

# 从环境变量获取配置
JWT_SECRET = os.getenv("MANAGEMENT_JWT_SECRET", "your-secret-key")
SUPER_ADMIN_USER_ID = os.getenv("SUPER_ADMIN_USER_ID", "d807e79c13a44c0391df3750fe82090b")


def get_current_user_from_token():
    """
    从请求头的 JWT token 中解析当前用户信息
    返回: dict 包含 user_id, is_super_admin, is_system_admin
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]  # 移除 'Bearer ' 前缀
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'is_super_admin': payload.get('is_super_admin', False),
            'is_system_admin': payload.get('is_system_admin', False)
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_super_admin(f):
    """
    装饰器：要求超级管理员权限
    只有超级管理员可以访问被装饰的端点
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_token()
        
        if not user:
            return jsonify({
                "code": 401,
                "message": "未授权访问，请先登录"
            }), 401
        
        if not user.get('is_super_admin'):
            return jsonify({
                "code": 403,
                "message": "权限不足，需要超级管理员权限"
            }), 403
        
        # 将用户信息存入 g 对象供后续使用
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """
    装饰器：要求管理员权限
    超级管理员或系统管理员都可以访问被装饰的端点
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user_from_token()
        
        if not user:
            return jsonify({
                "code": 401,
                "message": "未授权访问，请先登录"
            }), 401
        
        if not user.get('is_super_admin') and not user.get('is_system_admin'):
            return jsonify({
                "code": 403,
                "message": "权限不足，需要管理员权限"
            }), 403
        
        # 将用户信息存入 g 对象供后续使用
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function
