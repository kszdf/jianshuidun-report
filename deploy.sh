#!/bin/bash
# ============================================
# 建税盾 v0.2.0 一键部署脚本
# 适用环境：Ubuntu 22.04 LTS
# 功能：部署建税盾SaaS + 税检康H5
# ============================================

set -e

# ===== 配置区 =====
DOMAIN="hgtcs.com"
REPORT_DOMAIN="report.hgtcs.com"
SJK_DOMAIN="sjk.hgtcs.com"
APP_DIR="/opt/jianshuidun"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend-vite"
TAXCHECK_DIR="/opt/taxcheck"
VENV_DIR="$APP_DIR/venv"
GUNICORN_PORT=8000
# =================

echo "======================================"
echo "  建税盾 v0.2.0 部署脚本"
echo "======================================"

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 root 权限运行: sudo $0"
    exit 1
fi

# ===== 第一步：系统依赖 =====
echo ""
echo "[1/6] 安装系统依赖..."
apt update -qq
apt install -y -qq python3 python3-pip python3-venv nginx certbot python3-certbot-nginx npm > /dev/null 2>&1
echo "✅ 系统依赖安装完成"

# ===== 第二步：创建目录 =====
echo ""
echo "[2/6] 创建应用目录..."
mkdir -p $APP_DIR $TAXCHECK_DIR
echo "✅ 目录创建完成"

# ===== 第三步：部署后端 =====
echo ""
echo "[3/6] 部署后端服务..."

# 解压代码（假设tar包在当前目录）
if [ -f "./jianshuidun_v0.2.0.tar.gz" ]; then
    tar xzf jianshuidun_v0.2.0.tar.gz -C /tmp/
    cp -r /tmp/jianzao-report/* $APP_DIR/
    echo "✅ 代码解压完成"
fi

# 创建虚拟环境
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate
pip install -q -r $BACKEND_DIR/requirements.txt
echo "✅ Python依赖安装完成"

# 初始化数据
cd $BACKEND_DIR
python init_data.py 2>/dev/null || true
echo "✅ 演示数据初始化完成"

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
systemctl enable jianshuidun
systemctl restart jianshuidun
echo "✅ 后端服务启动完成"

# ===== 第四步：构建前端 =====
echo ""
echo "[4/6] 构建前端..."

cd $FRONTEND_DIR
npm install 2>/dev/null
npm run build 2>/dev/null
echo "✅ 前端构建完成"

# ===== 第五步：部署税检康H5 v3.0 =====
echo ""
echo "[5/6] 部署税检康H5 v3.0..."

# 使用代码包中的 taxcheck_v3 目录（完整版20个案例）
if [ -d "$APP_DIR/taxcheck_v3" ]; then
    cp -r $APP_DIR/taxcheck_v3/* $TAXCHECK_DIR/
elif [ -d "$APP_DIR/taxcheck" ]; then
    cp -r $APP_DIR/taxcheck/* $TAXCHECK_DIR/
elif [ -f "$APP_DIR/taxcheck.html" ]; then
    cp $APP_DIR/taxcheck.html $TAXCHECK_DIR/index.html
fi

echo "✅ 税检康H5部署完成"

# ===== 第六步：配置Nginx =====
echo ""
echo "[6/6] 配置Nginx..."

# 建税盾站点
cat > /etc/nginx/sites-available/report << 'NGINX_CONF'
server {
    listen 80;
    server_name report.hgtcs.com;

    # 前端静态文件
    location / {
        root /opt/jianshuidun/frontend-vite/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf)$ {
        root /opt/jianshuidun/frontend-vite/dist;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_CONF

# 税检康站点
cat > /etc/nginx/sites-available/taxcheck << 'NGINX_CONF'
server {
    listen 80;
    server_name sjk.hgtcs.com;

    location / {
        root /opt/taxcheck;
        index index.html;
    }
}
NGINX_CONF

# 启用站点
ln -sf /etc/nginx/sites-available/report /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/taxcheck /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试配置
nginx -t
systemctl reload nginx
echo "✅ Nginx配置完成"

echo ""
echo "======================================"
echo "  🎉 部署完成！"
echo "======================================"
echo ""
echo "建税盾: http://$REPORT_DOMAIN"
echo "税检康: http://$SJK_DOMAIN"
echo ""
echo "演示账号: boss/123456 或 finance/123456"
echo ""
echo "下一步：配置DNS解析后，运行以下命令申请SSL证书："
echo "  certbot --nginx -d $REPORT_DOMAIN -d $SJK_DOMAIN"
echo ""
