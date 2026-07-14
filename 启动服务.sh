#!/bin/bash
clear

echo ""
echo "========================================"
echo "  建税盾建筑经营管理报表系统"
echo "  一键启动脚本 (Mac/Linux)"
echo "========================================"
echo ""

cd "$(dirname "$0")/backend"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[X] 未检测到Python3，请先安装Python 3.10+"
    echo "Mac: brew install python3"
    echo "Ubuntu: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo "[√] Python 已安装"
python3 --version

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo ""
    echo "[*] 首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[X] 虚拟环境创建失败"
        exit 1
    fi
    echo "[√] 虚拟环境创建成功"
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if ! python -c "import fastapi" &> /dev/null; then
    echo ""
    echo "[*] 正在安装依赖（第一次比较慢，请耐心等待）..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[X] 依赖安装失败"
        exit 1
    fi
    echo "[√] 依赖安装成功"
fi

# 检查数据库
if [ ! -f "data/jianzao.db" ]; then
    echo ""
    echo "[*] 正在初始化数据库和演示数据..."
    mkdir -p data
    python init_data.py
    if [ $? -ne 0 ]; then
        echo "[X] 初始化失败"
        exit 1
    fi
    echo "[√] 初始化完成"
fi

echo ""
echo "========================================"
echo "  服务启动中..."
echo "  访问地址: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  演示账号: boss / 123456"
echo "  按 Ctrl+C 停止服务"
echo "========================================"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000
