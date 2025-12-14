#!/bin/bash
# ===================================
# RAGFlow-Plus 混合部署启动脚本
# 中间件 Docker + 源码部署
# ===================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "  RAGFlow-Plus 混合部署启动脚本"
echo "============================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ $1 未安装${NC}"
        return 1
    fi
    return 0
}

# 启动中间件
start_middleware() {
    echo ""
    echo -e "${YELLOW}📦 启动中间件服务 (Docker)...${NC}"
    
    MIDDLEWARE_DIR="$PROJECT_ROOT/docker"
    
    if [ ! -f "$MIDDLEWARE_DIR/docker-compose-base.yml" ]; then
        echo -e "${RED}❌ 未找到 docker-compose-base.yml${NC}"
        return 1
    fi
    
    cd "$MIDDLEWARE_DIR"
    docker compose -f docker-compose-base.yml up -d
    
    echo -e "${GREEN}✅ 中间件已启动${NC}"
    echo "   等待中间件就绪..."
    sleep 15
}

# 启动主后端
start_main_backend() {
    echo ""
    echo -e "${YELLOW}🔧 启动主后端服务...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo "   创建虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # 安装依赖（如果需要）
    if [ ! -f "venv/.installed" ]; then
        echo "   安装依赖..."
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
        touch venv/.installed
    fi
    
    echo "   启动 API 服务..."
    nohup python -m api.ragflow_server > logs/ragflow_api.log 2>&1 &
    echo $! > logs/ragflow_api.pid
    
    echo -e "${GREEN}✅ 主后端已启动 (PID: $(cat logs/ragflow_api.pid))${NC}"
}

# 启动管理后台后端
start_management_backend() {
    echo ""
    echo -e "${YELLOW}🔧 启动管理后台后端...${NC}"
    
    cd "$PROJECT_ROOT/management/server"
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo "   创建虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # 安装依赖
    if [ ! -f "venv/.installed" ]; then
        echo "   安装依赖..."
        pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q
        touch venv/.installed
    fi
    
    echo "   启动管理后台 API..."
    mkdir -p logs
    nohup python app.py > logs/management_api.log 2>&1 &
    echo $! > logs/management_api.pid
    
    echo -e "${GREEN}✅ 管理后台后端已启动 (PID: $(cat logs/management_api.pid))${NC}"
}

# 启动前端（开发模式）
start_frontend_dev() {
    echo ""
    echo -e "${YELLOW}🌐 启动前端服务 (开发模式)...${NC}"
    
    # 启动前台前端
    cd "$PROJECT_ROOT/web"
    if [ ! -d "node_modules" ]; then
        echo "   安装前台前端依赖..."
        pnpm install
    fi
    mkdir -p logs
    nohup pnpm dev --host 0.0.0.0 --port 5173 > logs/frontend.log 2>&1 &
    echo $! > logs/frontend.pid
    echo -e "${GREEN}✅ 前台前端已启动: http://localhost:5173${NC}"
    
    # 启动管理后台前端
    cd "$PROJECT_ROOT/management/web"
    if [ ! -d "node_modules" ]; then
        echo "   安装管理后台前端依赖..."
        pnpm install
    fi
    mkdir -p logs
    nohup pnpm dev --host 0.0.0.0 --port 5174 > logs/frontend.log 2>&1 &
    echo $! > logs/frontend.pid
    echo -e "${GREEN}✅ 管理后台前端已启动: http://localhost:5174${NC}"
}

# 主函数
main() {
    # 检查必要命令
    echo "🔍 检查环境..."
    check_command docker || exit 1
    check_command python3 || exit 1
    check_command pnpm || exit 1
    echo -e "${GREEN}✅ 环境检查通过${NC}"
    
    # 创建日志目录
    mkdir -p "$PROJECT_ROOT/logs"
    
    # 按顺序启动服务
    start_middleware
    start_main_backend
    start_management_backend
    start_frontend_dev
    
    echo ""
    echo "============================================"
    echo -e "${GREEN}  ✅ 所有服务已启动！${NC}"
    echo "============================================"
    echo ""
    echo "  前台前端:     http://localhost:5173"
    echo "  管理后台前端: http://localhost:5174"
    echo "  主后端 API:   http://localhost:9380"
    echo "  管理后台 API: http://localhost:5000"
    echo ""
    echo "  MinIO 控制台: http://localhost:9001"
    echo ""
    echo "  日志目录: $PROJECT_ROOT/logs/"
    echo ""
    echo "  停止服务: ./scripts/stop_hybrid.sh"
    echo ""
}

main "$@"
