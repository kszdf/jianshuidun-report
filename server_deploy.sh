#!/bin/bash
# ============================================
# 建税盾 v0.2.0 服务器一键部署脚本
# 直接从GitHub拉取代码，全自动部署
# 使用方式：bash <(curl -sL 脚本原始地址)
# ============================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "======================================"
echo "  建税盾 v0.2.0 一键部署"
echo "  建税盾SaaS + 税检康H5"
echo "======================================"
echo -e "${NC}"

# 检查root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}请使用 root 权限运行${NC}"
    exit 1
fi

# ===== 配置 =====
GITHUB_REPO="kszdf/jianshuidun-report"
GITHUB_BRANCH="main"
APP_DIR="/opt/jianshuidun"
TAXCHECK_DIR="/opt/taxcheck"
VENV_DIR="$APP_DIR/venv"
GUNICORN_PORT=8000
REPORT_DOMAIN="report.hgtcs.com"
SJK_DOMAIN="sjk.hgtcs.com"

START_TIME=$(date +%s)

# ===== 1. 系统依赖 =====
echo ""
echo -e "${YELLOW}[1/7] 安装系统依赖...${NC}"
apt update -qq 2>/dev/null
apt install -y -qq python3 python3-pip python3-venv nginx certbot python3-certbot-nginx npm git curl > /dev/null 2>&1
echo -e "${GREEN}✅ 系统依赖安装完成${NC}"

# ===== 2. 拉取代码 =====
echo ""
echo -e "${YELLOW}[2/7] 从GitHub拉取代码...${NC}"
mkdir -p $APP_DIR

if [ -d "$APP_DIR/.git" ]; then
    cd $APP_DIR
    git fetch origin $GITHUB_BRANCH 2>/dev/null
    git reset --hard origin/$GITHUB_BRANCH 2>/dev/null
else
    rm -rf $APP_DIR
    git clone --depth 1 -b $GITHUB_BRANCH https://github.com/$GITHUB_REPO.git $APP_DIR 2>/dev/null
fi

echo -e "${GREEN}✅ 代码拉取完成${NC}"

# ===== 3. 后端部署 =====
echo ""
echo -e "${YELLOW}[3/7] 部署后端服务...${NC}"

BACKEND_DIR="$APP_DIR/backend"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
pip install -q -r $BACKEND_DIR/requirements.txt 2>/dev/null

# 初始化数据
cd $BACKEND_DIR
python init_data.py 2>/dev/null || true

# 创建Gunicorn服务
cat > /etc/systemd/system/jianshuidun.service << EOF
[Unit]
Description=Jianshuidun Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONPATH=$BACKEND_DIR"
ExecStart=$VENV_DIR/bin/gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:$GUNICORN_PORT --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable jianshuidun 2>/dev/null
systemctl restart jianshuidun

# 等待后端启动
sleep 2
if curl -s http://127.0.0.1:$GUNICORN_PORT/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务启动成功${NC}"
else
    echo -e "${YELLOW}⚠️  后端启动可能较慢，稍后自动验证${NC}"
fi

# ===== 4. 前端构建 =====
echo ""
echo -e "${YELLOW}[4/7] 构建前端（约3-5分钟）...${NC}"

FRONTEND_DIR="$APP_DIR/frontend-vite"
cd $FRONTEND_DIR

npm install 2>&1 | tail -1
npm run build 2>&1 | tail -3

if [ -d "dist" ]; then
    echo -e "${GREEN}✅ 前端构建完成${NC}"
else
    echo -e "${RED}❌ 前端构建失败，请检查错误信息${NC}"
    exit 1
fi

# ===== 5. 税检康H5 =====
echo ""
echo -e "${YELLOW}[5/7] 部署税检康H5 v3.0...${NC}"

mkdir -p $TAXCHECK_DIR

if [ -d "$APP_DIR/taxcheck_v3" ]; then
    cp -r $APP_DIR/taxcheck_v3/* $TAXCHECK_DIR/
elif [ -d "$APP_DIR/taxcheck" ]; then
    cp -r $APP_DIR/taxcheck/* $TAXCHECK_DIR/
fi

echo -e "${GREEN}✅ 税检康H5部署完成${NC}"

# ===== 6. Nginx配置 =====
echo ""
echo -e "${YELLOW}[6/7] 配置Nginx...${NC}"

# 建税盾站点
cat > /etc/nginx/sites-available/report << 'NGINX_EOF'
server {
    listen 80;
    server_name report.hgtcs.com;

    location / {
        root /opt/jianshuidun/frontend-vite/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        root /opt/jianshuidun/frontend-vite/dist;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# 税检康站点
cat > /etc/nginx/sites-available/taxcheck << 'NGINX_EOF'
server {
    listen 80;
    server_name sjk.hgtcs.com;

    location / {
        root /opt/taxcheck;
        index index.html;
    }
}
NGINX_EOF

# 启用站点
ln -sf /etc/nginx/sites-available/report /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/taxcheck /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

if nginx -t 2>/dev/null; then
    systemctl reload nginx
    echo -e "${GREEN}✅ Nginx配置完成${NC}"
else
    echo -e "${RED}❌ Nginx配置有误${NC}"
    nginx -t
    exit 1
fi

# ===== 7. 验证 =====
echo ""
echo -e "${YELLOW}[7/7] 部署验证...${NC}"

# 后端验证
sleep 1
BACKEND_OK="❌"
if curl -s http://127.0.0.1:$GUNICORN_PORT/api/taxcheck/health | grep -q "ok"; then
    BACKEND_OK="✅"
fi

# 前端验证
FRONTEND_OK="❌"
if [ -f "$FRONTEND_DIR/dist/index.html" ]; then
    FRONTEND_OK="✅"
fi

# H5验证
H5_OK="❌"
if [ -f "$TAXCHECK_DIR/index.html" ]; then
    H5_OK="✅"
fi

# Nginx验证
NGINX_OK="❌"
if systemctl is-active --quiet nginx; then
    NGINX_OK="✅"
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "======================================"
echo -e "${GREEN}  🎉 部署完成！耗时 ${DURATION} 秒${NC}"
echo "======================================"
echo ""
echo "  后端服务:  $BACKEND_OK  http://127.0.0.1:8000"
echo "  前端构建:  $FRONTEND_OK  $FRONTEND_DIR/dist"
echo "  税检康H5:  $H5_OK  $TAXCHECK_DIR"
echo "  Nginx:     $NGINX_OK"
echo ""
echo "  建税盾SaaS:  http://$REPORT_DOMAIN"
echo "  税检康H5:    http://$SJK_DOMAIN"
echo ""
echo "  演示账号: boss/123456 或 finance/123456"
echo ""
echo -e "${YELLOW}  DNS解析生效后，执行以下命令申请HTTPS证书：${NC}"
echo "  certbot --nginx -d $REPORT_DOMAIN -d $SJK_DOMAIN"
echo ""
echo "======================================"
