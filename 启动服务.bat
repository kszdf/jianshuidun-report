@echo off
chcp 65001 >nul
title 建税盾报表系统 - 启动服务
color 0A

echo.
echo ========================================
echo   建税盾建筑经营管理报表系统
echo   一键启动脚本 (Windows)
echo ========================================
echo.

cd /d "%~dp0backend"

REM 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [X] 未检测到Python，请先安装Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [√] Python 已安装
python --version

REM 检查虚拟环境
if not exist "venv" (
    echo.
    echo [*] 首次运行，正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [X] 虚拟环境创建失败
        pause
        exit /b 1
    )
    echo [√] 虚拟环境创建成功
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 检查依赖
if not exist "venv\Lib\site-packages\fastapi" (
    echo.
    echo [*] 正在安装依赖（第一次比较慢，请耐心等待）...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [X] 依赖安装失败
        pause
        exit /b 1
    )
    echo [√] 依赖安装成功
)

REM 检查数据库
if not exist "data\jianzao.db" (
    echo.
    echo [*] 正在初始化数据库和演示数据...
    if not exist "data" mkdir data
    python init_data.py
    if %errorlevel% neq 0 (
        echo [X] 初始化失败
        pause
        exit /b 1
    )
    echo [√] 初始化完成
)

echo.
echo ========================================
echo   服务启动中...
echo   访问地址: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo   演示账号: boss / 123456
echo   按 Ctrl+C 停止服务
echo ========================================
echo.

uvicorn main:app --host 0.0.0.0 --port 8000

pause
