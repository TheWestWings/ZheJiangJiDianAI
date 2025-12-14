# RAGFlow-Plus 混合部署指南（中间件 Docker + 源码部署）

本文档介绍如何使用 **Docker 部署中间件**（MySQL、Redis、MinIO、Elasticsearch）+ **源码部署应用服务**（前端、后端）的混合部署方式。

---

## 目录

- [1. 部署架构](#1-部署架构)
- [2. 环境准备](#2-环境准备)
- [3. 部署中间件（Docker）](#3-部署中间件docker)
- [4. 部署主后端服务（源码）](#4-部署主后端服务源码)
- [5. 部署前台前端（源码）](#5-部署前台前端源码)
- [6. 部署管理后台（源码）](#6-部署管理后台源码)
- [7. Nginx 配置](#7-nginx-配置)
- [8. 服务管理](#8-服务管理)

---

## 1. 部署架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx (反向代理)                         │
│                     80/443 → 前端/API                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
    ▼                          ▼                          ▼
┌────────────┐          ┌────────────┐          ┌────────────┐
│  前台前端   │          │ 管理后台前端 │          │ 管理后台后端 │
│  (源码)    │          │   (源码)    │          │   (源码)    │
│  :5173    │          │   :5174     │          │   :5000    │
└────────────┘          └────────────┘          └────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │   主后端 API      │
                    │    (源码)        │
                    │     :9380        │
                    └────────┬─────────┘
                             │
    ┌────────────┬───────────┼───────────┬────────────┐
    │            │           │           │            │
    ▼            ▼           ▼           ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ MySQL  │  │ Redis  │  │ MinIO  │  │   ES   │  │ Kibana │
│ Docker │  │ Docker │  │ Docker │  │ Docker │  │ Docker │
│ :5455  │  │ :6379  │  │ :9000  │  │ :1200  │  │ :6601  │
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘
```

---

## 2. 环境准备

### 2.1 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ |
| CPU | 4 核+ |
| 内存 | 16 GB+ |
| 磁盘 | 100 GB+ (SSD) |

### 2.2 软件依赖

```bash
# Docker（用于中间件）
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker

# Node.js 18+（用于前端）
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g pnpm

# Python 3.10+（用于后端）
sudo apt-get install -y python3.10 python3.10-venv python3-pip

# Nginx（用于反向代理）
sudo apt-get install -y nginx
```

---

## 3. 部署中间件（Docker）

### 3.1 创建中间件配置文件

创建 `docker-compose-middleware.yml`：

```yaml
version: '3.8'

services:
  # Elasticsearch
  es01:
    container_name: ragflow-es-01
    image: elasticsearch:8.11.3
    volumes:
      - esdata01:/usr/share/elasticsearch/data
    ports:
      - "1200:9200"
    environment:
      - node.name=es01
      - ELASTIC_PASSWORD=infini_rag_flow
      - bootstrap.memory_lock=false
      - discovery.type=single-node
      - xpack.security.enabled=true
      - xpack.security.http.ssl.enabled=false
      - xpack.security.transport.ssl.enabled=false
      - cluster.routing.allocation.disk.watermark.low=5gb
      - cluster.routing.allocation.disk.watermark.high=3gb
      - cluster.routing.allocation.disk.watermark.flood_stage=2gb
      - TZ=Asia/Shanghai
    mem_limit: 8073741824
    healthcheck:
      test: ["CMD-SHELL", "curl http://localhost:9200"]
      interval: 10s
      timeout: 10s
      retries: 120
    networks:
      - ragflow
    restart: on-failure

  # MySQL
  mysql:
    image: mysql:8.0.39
    container_name: ragflow-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=infini_rag_flow
      - TZ=Asia/Shanghai
    command:
      --max_connections=1000
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --default-authentication-plugin=mysql_native_password
      --tls_version="TLSv1.2,TLSv1.3"
      --init-file=/data/application/init.sql
    ports:
      - "5455:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/data/application/init.sql
    networks:
      - ragflow
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-uroot", "-pinfini_rag_flow"]
      interval: 10s
      timeout: 10s
      retries: 3
    restart: on-failure

  # MinIO
  minio:
    image: quay.io/minio/minio:RELEASE.2025-06-13T11-33-47Z
    container_name: ragflow-minio
    command: server --console-address ":9001" /data
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=rag_flow
      - MINIO_ROOT_PASSWORD=infini_rag_flow
      - TZ=Asia/Shanghai
    volumes:
      - minio_data:/data
    networks:
      - ragflow
    restart: on-failure

  # Redis (Valkey)
  redis:
    image: valkey/valkey:8
    container_name: ragflow-redis
    command: redis-server --requirepass infini_rag_flow --maxmemory 128mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - ragflow
    restart: on-failure

volumes:
  esdata01:
    driver: local
  mysql_data:
    driver: local
  minio_data:
    driver: local
  redis_data:
    driver: local

networks:
  ragflow:
    driver: bridge
```

### 3.2 创建初始化 SQL

创建 `init.sql`：

```sql
CREATE DATABASE IF NOT EXISTS rag_flow;
```

### 3.3 启动中间件

```bash
# 创建目录
mkdir -p ~/ragflow-middleware
cd ~/ragflow-middleware

# 创建上述两个文件后启动
docker compose -f docker-compose-middleware.yml up -d

# 验证中间件状态
docker compose -f docker-compose-middleware.yml ps
```

### 3.4 验证中间件连接

```bash
# 测试 MySQL
mysql -h 127.0.0.1 -P 5455 -u root -pinfini_rag_flow -e "SHOW DATABASES;"

# 测试 Redis
redis-cli -h 127.0.0.1 -p 6379 -a infini_rag_flow PING

# 测试 Elasticsearch
curl -u elastic:infini_rag_flow http://localhost:1200

# 测试 MinIO（访问控制台）
# 浏览器打开 http://your_ip:9001
# 用户名: rag_flow, 密码: infini_rag_flow
```

---

## 4. 部署主后端服务（源码）

### 4.1 克隆代码

```bash
git clone https://github.com/zstar1003/ragflow-plus.git
cd ragflow-plus
```

### 4.2 创建 Python 虚拟环境

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 4.3 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 4.4 配置服务

编辑 `conf/service_conf.yaml`：

```yaml
# 数据库配置（使用 Docker 中间件的地址）
mysql:
  host: 127.0.0.1
  port: 5455
  user: root
  password: infini_rag_flow
  database: rag_flow

# Redis 配置
redis:
  host: 127.0.0.1
  port: 6379
  password: infini_rag_flow

# MinIO 配置
minio:
  host: 127.0.0.1
  port: 9000
  user: rag_flow
  password: infini_rag_flow

# Elasticsearch 配置
es:
  host: 127.0.0.1
  port: 1200
  user: elastic
  password: infini_rag_flow
```

### 4.5 启动后端服务

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务（开发模式）
python -m api.ragflow_server

# 或使用 Gunicorn（生产模式）
gunicorn -w 4 -b 0.0.0.0:9380 api.ragflow_server:app
```

### 4.6 使用 systemd 管理服务（推荐）

创建 `/etc/systemd/system/ragflow-api.service`：

```ini
[Unit]
Description=RAGFlow API Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ragflow-plus
Environment="PATH=/path/to/ragflow-plus/venv/bin"
ExecStart=/path/to/ragflow-plus/venv/bin/python -m api.ragflow_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start ragflow-api
sudo systemctl enable ragflow-api
sudo systemctl status ragflow-api
```

---

## 5. 部署前台前端（源码）

### 5.1 安装依赖并构建

```bash
cd ragflow-plus/web

# 安装依赖
pnpm install

# 开发模式（热更新）
pnpm dev --host 0.0.0.0 --port 5173

# 或生产模式（构建静态文件）
pnpm build
```

### 5.2 生产部署（使用 Nginx）

构建后的静态文件在 `web/dist` 目录，配置 Nginx 提供服务。

---

## 6. 部署管理后台（源码）

### 6.1 部署管理后台前端

```bash
cd ragflow-plus/management/web

# 安装依赖
pnpm install

# 配置 API 地址
# 编辑 .env 文件
echo "VITE_API_BASE_URL=http://127.0.0.1:5000/api" > .env.local

# 开发模式
pnpm dev --host 0.0.0.0 --port 5174

# 或生产模式
pnpm build
```

### 6.2 部署管理后台后端

```bash
cd ragflow-plus/management/server

# 创建虚拟环境
python3.10 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6.3 配置管理后台后端

编辑 `management/.env`：

```bash
# MySQL 配置（使用 Docker 中间件）
MYSQL_HOST=127.0.0.1
MYSQL_PORT=5455
MYSQL_DBNAME=rag_flow
MYSQL_PASSWORD=infini_rag_flow

# 管理员配置
SUPER_ADMIN_USER_ID=your_admin_user_id
MANAGEMENT_JWT_SECRET=your_jwt_secret
```

### 6.4 启动管理后台后端

```bash
source venv/bin/activate
python app.py
```

### 6.5 使用 systemd 管理（推荐）

创建 `/etc/systemd/system/ragflow-management.service`：

```ini
[Unit]
Description=RAGFlow Management Backend
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ragflow-plus/management/server
Environment="PATH=/path/to/ragflow-plus/management/server/venv/bin"
ExecStart=/path/to/ragflow-plus/management/server/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start ragflow-management
sudo systemctl enable ragflow-management
```

---

## 7. Nginx 配置

### 7.1 主站配置

创建 `/etc/nginx/sites-available/ragflow`：

```nginx
# 前台 Web
server {
    listen 80;
    server_name your_domain.com;
    
    # 前端静态文件（生产模式）
    root /path/to/ragflow-plus/web/dist;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain application/javascript text/css application/json;

    # API 代理
    location ~ ^/(v1|api) {
        proxy_pass http://127.0.0.1:9380;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~ ^/static/ {
        expires 10y;
        access_log off;
    }
}

# 管理后台
server {
    listen 8888;
    server_name your_domain.com;

    root /path/to/ragflow-plus/management/web/dist;
    index index.html;
    
    client_max_body_size 500M;

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 前端路由
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 7.2 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/ragflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 8. 服务管理

### 8.1 启动顺序

```bash
# 1. 启动中间件
cd ~/ragflow-middleware
docker compose -f docker-compose-middleware.yml up -d

# 2. 启动主后端 API
sudo systemctl start ragflow-api

# 3. 启动管理后台后端
sudo systemctl start ragflow-management

# 4. 启动 Nginx
sudo systemctl start nginx
```

### 8.2 查看状态

```bash
# 中间件状态
docker compose -f docker-compose-middleware.yml ps

# 服务状态
sudo systemctl status ragflow-api
sudo systemctl status ragflow-management
sudo systemctl status nginx
```

### 8.3 查看日志

```bash
# 中间件日志
docker logs -f ragflow-mysql
docker logs -f ragflow-redis
docker logs -f ragflow-es-01

# 服务日志
sudo journalctl -u ragflow-api -f
sudo journalctl -u ragflow-management -f
```

### 8.4 开发模式快速启动脚本

创建 `start_dev.sh`：

```bash
#!/bin/bash

# 启动中间件
echo "Starting middleware..."
cd ~/ragflow-middleware
docker compose -f docker-compose-middleware.yml up -d

# 等待中间件就绪
echo "Waiting for middleware..."
sleep 10

# 启动主后端
echo "Starting main backend..."
cd /path/to/ragflow-plus
source venv/bin/activate
python -m api.ragflow_server &

# 启动管理后台后端
echo "Starting management backend..."
cd /path/to/ragflow-plus/management/server
source venv/bin/activate
python app.py &

# 启动前台前端
echo "Starting frontend..."
cd /path/to/ragflow-plus/web
pnpm dev --host 0.0.0.0 --port 5173 &

# 启动管理后台前端
echo "Starting management frontend..."
cd /path/to/ragflow-plus/management/web
pnpm dev --host 0.0.0.0 --port 5174 &

echo "All services started!"
echo "Frontend: http://localhost:5173"
echo "Management: http://localhost:5174"
echo "API: http://localhost:9380"
```

```bash
chmod +x start_dev.sh
./start_dev.sh
```

---

## 密码汇总

| 服务 | 用户名 | 密码 |
|------|--------|------|
| MySQL | root | infini_rag_flow |
| Redis | - | infini_rag_flow |
| Elasticsearch | elastic | infini_rag_flow |
| MinIO | rag_flow | infini_rag_flow |

> ⚠️ **生产环境请务必修改所有默认密码！**
