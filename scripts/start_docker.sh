#!/bin/bash
# ===================================
# RAGFlow-Plus Docker 一键启动脚本
# ===================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/docker"

echo "============================================"
echo "  RAGFlow-Plus Docker 启动脚本"
echo "============================================"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查 .env 文件
if [ ! -f "$DOCKER_DIR/.env" ]; then
    echo "⚠️  未找到 .env 文件，正在从示例文件创建..."
    if [ -f "$DOCKER_DIR/.env.example" ]; then
        cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
        echo "✅ 已创建 .env 文件，请修改配置后重新运行此脚本"
        echo "   配置文件位置: $DOCKER_DIR/.env"
        exit 1
    else
        echo "❌ 未找到 .env.example 文件"
        exit 1
    fi
fi

cd "$DOCKER_DIR"

echo ""
echo "📦 正在拉取 Docker 镜像..."
docker compose pull

echo ""
echo "🚀 正在启动服务..."
docker compose up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 10

echo ""
echo "📊 服务状态:"
docker compose ps

echo ""
echo "============================================"
echo "  ✅ RAGFlow-Plus 启动成功！"
echo "============================================"
echo ""
echo "  前台界面: http://localhost:80"
echo "  管理后台: http://localhost:8888"
echo "  API 服务: http://localhost:9380"
echo ""
echo "  MinIO 控制台: http://localhost:9001"
echo ""
echo "  查看日志: docker compose logs -f"
echo "  停止服务: docker compose down"
echo ""
