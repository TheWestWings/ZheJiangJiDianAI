import logging
import os
from datetime import datetime, timedelta

import jwt
from dotenv import load_dotenv
from flask import Flask, request, g
from flask_cors import CORS
from routes import register_routes
from middleware.permission import get_current_user_from_token

# 加载环境变量 - 优先加载 management/.env
management_env = os.path.join(os.path.dirname(__file__), "..", ".env")
docker_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docker", ".env")

if os.path.exists(management_env):
    load_dotenv(management_env)
elif os.path.exists(docker_env):
    load_dotenv(docker_env)

app = Flask(__name__)
# 启用CORS，允许前端访问
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})

# 注册所有路由
register_routes(app)


# 请求拦截器：解析 JWT token 并存入 g 对象
@app.before_request
def before_request():
    """在每个请求前解析 JWT token"""
    # 跳过登录接口和OPTIONS请求
    if request.path == '/api/v1/auth/login' or request.method == 'OPTIONS':
        return
    
    user = get_current_user_from_token()
    if user:
        g.user_id = user.get('user_id')
        g.username = user.get('username')
        g.is_super_admin = user.get('is_super_admin', False)
        g.is_system_admin = user.get('is_system_admin', False)

# 从环境变量获取配置
ADMIN_USERNAME = os.getenv("MANAGEMENT_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("MANAGEMENT_ADMIN_PASSWORD", "12345678")
JWT_SECRET = os.getenv("MANAGEMENT_JWT_SECRET", "your-secret-key")


# 设置日志目录和文件名
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "parser.log")

# 配置 logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),  # 同时也输出到控制台
    ],
)


# 生成token
def generate_token(username, user_id=None, is_super_admin=False, is_system_admin=False):
    # 设置令牌过期时间（例如8小时后过期）
    expire_time = datetime.utcnow() + timedelta(hours=8)

    # 生成令牌
    payload = {
        "username": username, 
        "exp": expire_time,
        "is_super_admin": is_super_admin,
        "is_system_admin": is_system_admin
    }
    if user_id:
        payload["user_id"] = user_id
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return token


def verify_database_user(email, password):
    """验证数据库中的用户（用于系统管理员登录）"""
    from database import get_db_connection
    import base64
    from werkzeug.security import check_password_hash
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询用户
        cursor.execute("""
            SELECT id, nickname, email, password, is_system_admin 
            FROM user 
            WHERE email = %s AND status = 1
        """, (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return None, "用户不存在"
        
        # 验证密码 - 需要先 base64 编码再比较
        base64_password = base64.b64encode(password.encode()).decode()
        if not check_password_hash(user['password'], base64_password):
            return None, "密码错误"
        
        # 检查是否是系统管理员
        if not user.get('is_system_admin', 0):
            return None, "您没有后台管理权限"
        
        return user, None
    except Exception as e:
        print(f"数据库验证错误: {e}")
        return None, str(e)


# 登录路由保留在主文件中
@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"code": 1, "message": "用户名和密码不能为空"}, 400

    # 方式1: 检查是否是 .env 中的超级管理员
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        # 超级管理员登录
        token = generate_token(username, is_super_admin=True)
        return {"code": 0, "data": {"token": token}, "message": "登录成功"}

    # 方式2: 检查数据库中的系统管理员（使用邮箱登录）
    user, error = verify_database_user(username, password)  # username 此处作为 email 使用
    if user:
        token = generate_token(
            user['nickname'], 
            user_id=user['id'], 
            is_system_admin=True
        )
        return {"code": 0, "data": {"token": token}, "message": "登录成功"}
    
    # 都验证失败
    if error:
        return {"code": 1, "message": error}, 400
    
    return {"code": 1, "message": "用户名或密码错误"}, 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

