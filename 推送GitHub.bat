@echo off
chcp 65001 >nul
echo ========================================
echo   建税盾报表系统 - GitHub一键推送脚本
echo ========================================
echo.

set /p GH_USER=请输入你的GitHub用户名: 
set /p GH_REPO=请输入仓库名称(如 jianzao-report): 
set /p GH_TOKEN=请输入GitHub Personal Access Token: 

echo.
echo 正在初始化Git仓库...
git init
git add .
git commit -m "初始版本: 建税盾建筑经营管理报表系统 MVP v0.1.0"

echo.
echo 正在推送到GitHub...
git branch -M main
git remote add origin https://%GH_USER%:%GH_TOKEN%@github.com/%GH_USER%/%GH_REPO%.git
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ✅ 推送成功！
    echo 仓库地址: https://github.com/%GH_USER%/%GH_REPO%
) else (
    echo.
    echo ❌ 推送失败，请检查用户名、仓库名和Token是否正确
)

echo.
pause
