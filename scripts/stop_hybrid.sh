#!/bin/bash
# ===================================
# RAGFlow-Plus 混合部署停止脚本
# ===================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  RAGFlow-Plus 停止服务"
echo "============================================"

# 停止前台前端
if [ -f "$PROJECT_ROOT/web/logs/frontend.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/web/logs/frontend.pid")
    if kill -0 $PID 2>/dev/null; then
        echo "🛑 停止前台前端 (PID: $PID)..."
        kill $PID
    fi
    rm -f "$PROJECT_ROOT/web/logs/frontend.pid"
fi

# 停止管理后台前端
if [ -f "$PROJECT_ROOT/management/web/logs/frontend.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/management/web/logs/frontend.pid")
    if kill -0 $PID 2>/dev/null; then
        echo "🛑 停止管理后台前端 (PID: $PID)..."
        kill $PID
    fi
    rm -f "$PROJECT_ROOT/management/web/logs/frontend.pid"
fi

# 停止主后端
if [ -f "$PROJECT_ROOT/logs/ragflow_api.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/logs/ragflow_api.pid")
    if kill -0 $PID 2>/dev/null; then
        echo "🛑 停止主后端 API (PID: $PID)..."
        kill $PID
    fi
    rm -f "$PROJECT_ROOT/logs/ragflow_api.pid"
fi

# 停止管理后台后端
if [ -f "$PROJECT_ROOT/management/server/logs/management_api.pid" ]; then
    PID=$(cat "$PROJECT_ROOT/management/server/logs/management_api.pid")
    if kill -0 $PID 2>/dev/null; then
        echo "🛑 停止管理后台后端 (PID: $PID)..."
        kill $PID
    fi
    rm -f "$PROJECT_ROOT/management/server/logs/management_api.pid"
fi

# 停止中间件
echo ""
read -p "是否同时停止中间件 (Docker)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🛑 停止中间件..."
    cd "$PROJECT_ROOT/docker"
    docker compose -f docker-compose-base.yml down
fi

echo ""
echo "✅ 所有服务已停止"
