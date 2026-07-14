"""
建税盾·建筑经营管理报表系统
后端服务入口
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, report, import_data, config, tax_calc, project_accounting, taxcheck


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    Base.metadata.create_all(bind=engine)
    yield
    # 关闭时清理


app = FastAPI(
    title="建税盾·建筑经营管理报表系统 API",
    description="建筑工程企业专属经营管理报表系统后端API",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(report.router, prefix="/api/report", tags=["报表"])
app.include_router(import_data.router, prefix="/api/import", tags=["数据导入"])
app.include_router(config.router, prefix="/api/config", tags=["配置"])
app.include_router(tax_calc.router, prefix="/api/tax", tags=["税务计算"])
app.include_router(project_accounting.router, prefix="/api/project-accounting", tags=["项目核算"])
app.include_router(taxcheck.router, prefix="/api/taxcheck", tags=["税检康"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "0.2.0"}


# ---------- 静态文件服务（前端页面） ----------
# 优先从 frontend-vite/dist 找（构建后的工程化版本），找不到就用 frontend/ 的CDN版
_frontend_dir = None
_vite_dist = os.path.join(os.path.dirname(__file__), "..", "frontend-vite", "dist")
_cdn_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")

if os.path.isdir(_vite_dist):
    _frontend_dir = _vite_dist
elif os.path.isdir(_cdn_dir):
    _frontend_dir = _cdn_dir

if _frontend_dir:
    # 挂载静态资源
    app.mount("/assets", StaticFiles(directory=os.path.join(_frontend_dir, "assets")) if os.path.isdir(os.path.join(_frontend_dir, "assets")) else StaticFiles(directory=_frontend_dir), name="assets")

    @app.get("/")
    async def serve_index():
        """首页 - 返回前端页面"""
        index_path = os.path.join(_frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "建税盾报表系统后端API运行中，请访问 /docs 查看接口文档"}

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """SPA路由 fallback，刷新页面不404"""
        # API请求不处理
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return {"detail": "Not Found"}
        # 其他路径都返回index.html，让前端路由处理
        index_path = os.path.join(_frontend_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"detail": "Not Found"}
