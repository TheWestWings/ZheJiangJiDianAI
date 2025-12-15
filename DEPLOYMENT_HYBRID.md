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

### 2.2 安装 Docker

```bash
# 更新系统包
sudo apt-get update

# 安装 Docker
sudo apt-get install -y docker.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证 Docker 安装
docker --version
docker compose version
```

### 2.3 安装 Conda

```bash
# 下载 Miniconda 安装脚本
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh

# 运行安装脚本
bash miniconda.sh -b -p $HOME/miniconda3

# 初始化 Conda
$HOME/miniconda3/bin/conda init bash

# 重新加载 shell 配置
source ~/.bashrc

# 验证 Conda 安装
conda --version
```

### 2.4 安装 Node.js 和 pnpm

```bash
# 使用 NodeSource 安装 Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 验证 Node.js 安装
node --version
npm --version

# 安装 pnpm
npm install -g pnpm

# 验证 pnpm 安装
pnpm --version
```

### 2.5 安装 Nginx

```bash
# 安装 Nginx
sudo apt-get install -y nginx

# 启动 Nginx 服务
sudo systemctl start nginx
sudo systemctl enable nginx

# 验证 Nginx 安装
nginx -v
```

---

## 3. 部署中间件（Docker）

### 3.1 克隆项目代码

```bash
# 克隆项目
git clone https://github.com/zstar1003/ragflow-plus.git

# 进入项目目录
cd ragflow-plus
```

### 3.2 启动基础服务

使用项目自带的 `docker-compose-base.yml` 启动中间件服务：

```bash
# 进入 docker 目录
cd docker

# 启动基础中间件服务（MySQL、Redis、MinIO、Elasticsearch）
docker compose -f docker-compose-base.yml up -d

# 查看服务启动状态
docker compose -f docker-compose-base.yml ps

# 等待所有服务健康检查通过（约 30-60 秒）
echo "等待服务启动..."
sleep 30

# 检查各服务状态
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### 3.3 使用 init.sql 初始化数据库

项目已包含完整的数据库初始化脚本 `docker/init.sql`，MySQL 容器启动时会自动执行。如需手动初始化或重新导入：

```bash
# 方法一：MySQL 容器启动时自动初始化（默认行为）
# init.sql 已挂载到容器内 /data/application/init.sql
# MySQL 启动参数 --init-file 会自动执行该文件

# 方法二：手动导入数据库（适用于重新初始化）
# 进入 docker 目录
cd /path/to/ragflow-plus/docker

# 使用 mysql 客户端导入
mysql -h127.0.0.1 -P5455 -uroot -pinfini_rag_flow < init.sql

# 或使用 Docker 内的 mysql 客户端
docker exec -i ragflow-mysql mysql -uroot -pinfini_rag_flow < init.sql
```

### 3.4 验证中间件连接

```bash
# 测试 MySQL 连接
mysql -h127.0.0.1 -P5455 -uroot -pinfini_rag_flow -e "SHOW DATABASES;"

# 验证 rag_flow 数据库和表
mysql -h127.0.0.1 -P5455 -uroot -pinfini_rag_flow -e "USE rag_flow; SHOW TABLES;"

# 测试 Redis 连接
redis-cli -h127.0.0.1 -p6379 -a infini_rag_flow PING

# 测试 Elasticsearch 连接
curl -u elastic:infini_rag_flow http://localhost:1200

# 测试 MinIO 连接（访问控制台）
# 浏览器打开 http://your_ip:9001
# 用户名: rag_flow, 密码: infini_rag_flow
```

---

## 4. 部署主后端服务（源码）

### 4.1 创建 Conda 环境

```bash
# 进入项目根目录
cd /path/to/ragflow-plus

# 创建名为 ragflow 的 Conda 环境，指定 Python 3.10
conda create -n ragflow python=3.10 -y

# 激活 Conda 环境
conda activate ragflow

# 验证 Python 版本
python --version
# 应输出: Python 3.10.x
```

### 4.2 安装 Python 依赖

```bash
# 确保已激活 ragflow 环境
conda activate ragflow

# 进入项目根目录
cd /path/to/ragflow-plus

# 使用清华镜像源安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 验证关键包安装
pip list | grep -E "flask|peewee|mysql-connector"
```

### 4.3 配置服务

编辑 `conf/service_conf.yaml`，配置中间件连接信息：

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

### 4.4 启动后端服务

```bash
# 激活 Conda 环境
conda activate ragflow

# 进入项目根目录
cd /path/to/ragflow-plus

# 开发模式启动
python -m api.ragflow_server

# 或使用 Gunicorn 生产模式启动
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:9380 api.ragflow_server:app
```

### 4.5 使用 systemd 管理服务（推荐）

创建 `/etc/systemd/system/ragflow-api.service`：

```ini
[Unit]
Description=RAGFlow API Server
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ragflow-plus
Environment="PATH=/home/your_user/miniconda3/envs/ragflow/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/your_user/miniconda3/envs/ragflow/bin/python -m api.ragflow_server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ragflow-api

# 设置开机自启
sudo systemctl enable ragflow-api

# 查看服务状态
sudo systemctl status ragflow-api
```

---

## 5. 部署前台前端（源码）

### 5.1 安装依赖

```bash
# 进入前端目录
cd /path/to/ragflow-plus/web

# 安装依赖
pnpm install
```

### 5.2 开发模式启动

```bash
# 开发模式（热更新）
pnpm dev --host 0.0.0.0 --port 5173
```

### 5.3 生产模式构建

```bash
# 构建生产版本
pnpm build

# 构建后的静态文件在 web/dist 目录
ls -la dist/
```

---

## 6. 部署管理后台（源码）

### 6.1 部署管理后台前端

```bash
# 进入管理后台前端目录
cd /path/to/ragflow-plus/management/web

# 安装依赖
pnpm install

# 配置 API 地址
echo "VITE_API_BASE_URL=http://127.0.0.1:5000/api" > .env.local

# 开发模式启动
pnpm dev --host 0.0.0.0 --port 5174

# 或生产模式构建
pnpm build
```

### 6.2 创建管理后台后端 Conda 环境

```bash
# 创建独立的 Conda 环境
conda create -n ragflow-management python=3.10 -y

# 激活环境
conda activate ragflow-management

# 进入管理后台后端目录
cd /path/to/ragflow-plus/management/server

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
# 激活 Conda 环境
conda activate ragflow-management

# 进入管理后台后端目录
cd /path/to/ragflow-plus/management/server

# 启动服务
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
Environment="PATH=/home/your_user/miniconda3/envs/ragflow-management/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/your_user/miniconda3/envs/ragflow-management/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start ragflow-management

# 设置开机自启
sudo systemctl enable ragflow-management

# 查看服务状态
sudo systemctl status ragflow-management
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
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/ragflow /etc/nginx/sites-enabled/

# 测试 Nginx 配置
sudo nginx -t

# 重新加载 Nginx
sudo systemctl reload nginx
```

---

## 8. 服务管理

### 8.1 启动顺序

```bash
# 1. 启动中间件（Docker）
cd /path/to/ragflow-plus/docker
docker compose -f docker-compose-base.yml up -d

# 2. 等待中间件就绪
echo "等待中间件启动..."
sleep 30

# 3. 启动主后端 API
sudo systemctl start ragflow-api

# 4. 启动管理后台后端
sudo systemctl start ragflow-management

# 5. 启动 Nginx
sudo systemctl start nginx
```

### 8.2 查看状态

```bash
# 中间件状态
cd /path/to/ragflow-plus/docker
docker compose -f docker-compose-base.yml ps

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
docker logs -f ragflow-minio

# 服务日志
sudo journalctl -u ragflow-api -f
sudo journalctl -u ragflow-management -f
```

### 8.4 停止服务

```bash
# 停止应用服务
sudo systemctl stop ragflow-api
sudo systemctl stop ragflow-management

# 停止中间件
cd /path/to/ragflow-plus/docker
docker compose -f docker-compose-base.yml down
```

### 8.5 开发模式快速启动脚本

创建 `start_dev.sh`：

```bash
#!/bin/bash

PROJECT_DIR="/path/to/ragflow-plus"

# 启动中间件
echo "========== 启动中间件 =========="
cd $PROJECT_DIR/docker
docker compose -f docker-compose-base.yml up -d

# 等待中间件就绪
echo "等待中间件启动..."
sleep 30

# 启动主后端
echo "========== 启动主后端 =========="
cd $PROJECT_DIR
conda activate ragflow
python -m api.ragflow_server &
sleep 5

# 启动管理后台后端
echo "========== 启动管理后台后端 =========="
cd $PROJECT_DIR/management/server
conda activate ragflow-management
python app.py &
sleep 3

# 启动前台前端
echo "========== 启动前台前端 =========="
cd $PROJECT_DIR/web
pnpm dev --host 0.0.0.0 --port 5173 &

# 启动管理后台前端
echo "========== 启动管理后台前端 =========="
cd $PROJECT_DIR/management/web
pnpm dev --host 0.0.0.0 --port 5174 &

echo ""
echo "========== 所有服务已启动 =========="
echo "前台前端:     http://localhost:5173"
echo "管理后台前端: http://localhost:5174"
echo "主后端 API:   http://localhost:9380"
echo "管理后台 API: http://localhost:5000"
```

```bash
# 添加执行权限
chmod +x start_dev.sh

# 运行脚本
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
