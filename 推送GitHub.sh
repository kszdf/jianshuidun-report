#!/bin/bash
echo "========================================"
echo "  建税盾报表系统 - GitHub一键推送脚本"
echo "========================================"
echo ""

read -p "请输入你的GitHub用户名: " GH_USER
read -p "请输入仓库名称(如 jianzao-report): " GH_REPO
read -p "请输入GitHub Personal Access Token: " GH_TOKEN

echo ""
echo "正在初始化Git仓库..."
git init
git add .
git commit -m "初始版本: 建税盾建筑经营管理报表系统 MVP v0.1.0"

echo ""
echo "正在推送到GitHub..."
git branch -M main
git remote add origin https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${GH_REPO}.git
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功！"
    echo "仓库地址: https://github.com/${GH_USER}/${GH_REPO}"
else
    echo ""
    echo "❌ 推送失败，请检查用户名、仓库名和Token是否正确"
fi
