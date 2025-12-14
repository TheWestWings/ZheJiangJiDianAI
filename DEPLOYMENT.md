# RAGFlow-Plus 部署指南

## 目录

- [1. 环境要求](#1-环境要求)
- [2. 快速部署（推荐）](#2-快速部署推荐)
- [3. 自定义构建 Docker 镜像](#3-自定义构建-docker-镜像)
- [4. Nginx 配置详解](#4-nginx-配置详解)
- [5. 环境变量配置](#5-环境变量配置)
- [6. 服务管理](#6-服务管理)
- [7. 故障排查](#7-故障排查)

---

## 1. 环境要求

### 硬件要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8 GB | 16 GB+ |
| 磁盘 | 50 GB | 100 GB+ (SSD) |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, CentOS 7+)
- **Docker**: 20.10+ (`docker --version`)
- **Docker Compose**: 2.0+ (`docker compose version`)
- **Git**: 2.0+

### 端口要求

| 端口 | 服务 | 说明 |
|------|------|------|
| 80 | 前台 Web | RAGFlow 主界面 |
| 443 | HTTPS | SSL 加密访问 |
| 8888 | 管理后台 | 后台管理系统 |
| 9380 | API 服务 | 后端 API |
| 5455 | MySQL | 数据库 |
| 9000/9001 | MinIO | 对象存储 |
| 6379 | Redis | 缓存 |
| 1200 | Elasticsearch | 搜索引擎 |

---

## 2. 快速部署（推荐）

### 2.1 克隆项目

```bash
git clone https://github.com/zstar1003/ragflow-plus.git
cd ragflow-plus
```

### 2.2 配置环境变量

```bash
cd docker
cp .env.example .env  # 如果有示例文件
# 或直接编辑 .env 文件
vim .env
```

**重要配置项：**

```bash
# MySQL 密码
MYSQL_PASSWORD=your_secure_password

# 管理后台账号密码
MANAGEMENT_ADMIN_USERNAME=admin
MANAGEMENT_ADMIN_PASSWORD=your_admin_password

# JWT 密钥（用于管理后台 token 加密）
MANAGEMENT_JWT_SECRET=your_jwt_secret

# MinIO 访问地址（改为服务器 IP 或域名）
MINIO_VISIT_HOST=your_server_ip

# 时区
TIMEZONE='Asia/Shanghai'
```

### 2.3 启动服务

```bash
# 在 docker 目录下执行
docker compose up -d
```

### 2.4 验证部署

```bash
# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f ragflow
```

### 2.5 访问服务

| 服务 | 地址 | 默认账号 |
|------|------|----------|
| 前台界面 | http://your_ip:80 | 注册新用户 |
| 管理后台 | http://your_ip:8888 | admin / 12345678 |

---

## 3. 自定义构建 Docker 镜像

### 3.1 项目结构

```
ragflow-plus/
├── Dockerfile                    # 主服务 Dockerfile
├── docker/
│   ├── docker-compose.yml        # 编排文件
│   ├── docker-compose-base.yml   # 基础服务（MySQL、Redis、ES、MinIO）
│   ├── .env                      # 环境变量
│   └── nginx/
│       ├── nginx.conf            # Nginx 主配置
│       ├── ragflow.conf          # 前台 Nginx 配置
│       ├── management_nginx.conf # 管理后台 Nginx 配置
│       └── proxy.conf            # 代理配置
├── management/
│   ├── Dockerfile                # 管理系统 Dockerfile（多阶段构建）
│   ├── web/                      # 管理后台前端（Vue）
│   └── server/                   # 管理后台后端（Flask）
└── web/                          # 前台前端（React）
```

### 3.2 构建主服务镜像

```bash
# 在项目根目录
docker build -t your-registry/ragflowplus:v1.0.0 .
```

### 3.3 构建管理系统镜像

管理系统使用多阶段构建，一个 Dockerfile 生成前端和后端两个镜像：

**构建前端镜像：**

```bash
cd management
docker build --target frontend -t your-registry/ragflowplus-management-web:v1.0.0 .
```

**构建后端镜像：**

```bash
cd management
docker build --target backend -t your-registry/ragflowplus-management-server:v1.0.0 .
```

### 3.4 推送镜像到仓库

```bash
# 登录镜像仓库
docker login your-registry

# 推送镜像
docker push your-registry/ragflowplus:v1.0.0
docker push your-registry/ragflowplus-management-web:v1.0.0
docker push your-registry/ragflowplus-management-server:v1.0.0
```

### 3.5 使用自定义镜像部署

修改 `docker/.env` 文件：

```bash
RAGFLOW_IMAGE=your-registry/ragflowplus:v1.0.0
RAGFLOWPLUS_MANAGEMENT_WEB_IMAGE=your-registry/ragflowplus-management-web:v1.0.0
RAGFLOWPLUS_MANAGEMENT_SERVER_IMAGE=your-registry/ragflowplus-management-server:v1.0.0
```

---

## 4. Nginx 配置详解

### 4.1 前台服务配置 (ragflow.conf)

```nginx
server {
    listen 80;
    server_name _;
    root /ragflow/web/dist;

    # 启用 Gzip 压缩
    gzip on;
    gzip_min_length 1k;
    gzip_comp_level 9;
    gzip_types text/plain application/javascript application/x-javascript 
               text/css application/xml text/javascript;
    gzip_vary on;

    # API 请求转发到后端
    location ~ ^/(v1|api) {
        proxy_pass http://ragflow:9380;
        include proxy.conf;
    }

    # 前端静态文件
    location / {
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~ ^/static/(css|js|media)/ {
        expires 10y;
        access_log off;
    }
}
```

### 4.2 管理后台配置 (management_nginx.conf)

```nginx
server {
    listen 80;
    
    # 允许上传大文件
    client_max_body_size 500M;
    
    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API 请求转发到后端
    location /api/ {
        proxy_pass http://management-backend:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 4.3 配置 HTTPS

**创建 SSL 证书目录：**

```bash
mkdir -p docker/nginx/ssl
# 将证书文件放入该目录
# - your_domain.crt
# - your_domain.key
```

**修改 ragflow.conf 添加 HTTPS：**

```nginx
server {
    listen 80;
    server_name your_domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your_domain.com;

    ssl_certificate /etc/nginx/ssl/your_domain.crt;
    ssl_certificate_key /etc/nginx/ssl/your_domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... 其他配置保持不变
}
```

**修改 docker-compose.yml 挂载证书：**

```yaml
ragflow:
  volumes:
    - ./nginx/ssl:/etc/nginx/ssl:ro
```

---

## 5. 环境变量配置

### 5.1 完整配置参考

```bash
# ============ 基础服务配置 ============
# 文档引擎类型
DOC_ENGINE=elasticsearch

# ============ Elasticsearch 配置 ============
STACK_VERSION=8.11.3
ES_HOST=es01
ES_PORT=1200
ELASTIC_PASSWORD=your_es_password

# ============ MySQL 配置 ============
MYSQL_HOST=mysql
MYSQL_PORT=5455
MYSQL_DBNAME=rag_flow
MYSQL_PASSWORD=your_mysql_password

# ============ Redis 配置 ============
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# ============ MinIO 配置 ============
MINIO_HOST=minio
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_USER=rag_flow
MINIO_PASSWORD=your_minio_password
# 重要：改为服务器公网 IP 或域名
MINIO_VISIT_HOST=your_server_ip

# ============ 服务配置 ============
SVR_HTTP_PORT=9380
TIMEZONE='Asia/Shanghai'
HF_ENDPOINT=https://hf-mirror.com

# ============ Docker 镜像 ============
RAGFLOW_IMAGE=zstar1003/ragflowplus:v0.5.0
RAGFLOWPLUS_MANAGEMENT_WEB_IMAGE=zstar1003/ragflowplus-management-web:v0.5.0
RAGFLOWPLUS_MANAGEMENT_SERVER_IMAGE=zstar1003/ragflowplus-management-server:v0.5.0

# ============ 管理后台配置 ============
MANAGEMENT_ADMIN_USERNAME=admin
MANAGEMENT_ADMIN_PASSWORD=your_admin_password
MANAGEMENT_JWT_SECRET=your_jwt_secret
```

---

## 6. 服务管理

### 6.1 常用命令

```bash
cd docker

# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启单个服务
docker compose restart ragflow

# 查看服务状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f ragflow
docker compose logs -f management-frontend
docker compose logs -f management-backend

# 进入容器
docker exec -it ragflowplus-server bash
docker exec -it ragflowplus-management-backend bash
```

### 6.2 数据备份

```bash
# 备份 MySQL 数据
docker exec ragflowplus-mysql mysqldump -u root -p rag_flow > backup_$(date +%Y%m%d).sql

# 备份 MinIO 数据（文件存储）
docker cp ragflowplus-minio:/data ./minio_backup

# 备份 Elasticsearch 数据
# 建议使用 ES 快照功能
```

### 6.3 升级服务

```bash
cd docker

# 拉取最新镜像
docker compose pull

# 重新创建容器
docker compose up -d

# 或者指定版本升级
# 修改 .env 中的镜像版本号后执行
docker compose up -d
```

---

## 7. 故障排查

### 7.1 服务无法启动

```bash
# 查看容器日志
docker compose logs ragflow

# 检查端口占用
netstat -tlnp | grep 80
lsof -i:80

# 检查磁盘空间
df -h
```

### 7.2 数据库连接失败

```bash
# 检查 MySQL 容器状态
docker compose ps mysql

# 进入 MySQL 容器测试连接
docker exec -it ragflowplus-mysql mysql -u root -p

# 检查网络连通性
docker exec ragflowplus-server ping mysql
```

### 7.3 API 请求失败

```bash
# 检查后端服务日志
docker compose logs -f ragflow

# 测试 API 连通性
curl http://localhost:9380/api/health
```

### 7.4 文件上传失败

```bash
# 检查 MinIO 服务
docker compose ps minio

# 检查 Nginx 配置中的 client_max_body_size
# 确保足够大（默认 500M）
```

### 7.5 清理重建

```bash
# 停止并删除所有容器、网络
docker compose down

# 删除数据卷（慎用，会丢失数据！）
docker compose down -v

# 清理 Docker 缓存
docker system prune -a

# 重新启动
docker compose up -d
```

---

## 附录：服务架构图

```
                    ┌─────────────────┐
                    │     Nginx       │
                    │    (80/443)     │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   前台 Web    │  │  管理后台 Web │  │   API 服务   │
    │   (React)    │  │    (Vue)     │  │   (Flask)    │
    │     :80      │  │    :8888     │  │    :9380     │
    └──────────────┘  └──────────────┘  └──────┬───────┘
                                               │
           ┌───────────────┬───────────────┬───┴───────┐
           │               │               │           │
           ▼               ▼               ▼           ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐
    │    MySQL     │ │    Redis     │ │  MinIO   │ │    ES    │
    │    :5455     │ │    :6379     │ │ :9000    │ │  :1200   │
    └──────────────┘ └──────────────┘ └──────────┘ └──────────┘
```
