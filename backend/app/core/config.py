"""
配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "建税盾·建筑经营管理报表系统"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # 数据库配置 - 默认用SQLite，方便开发；上线切换PostgreSQL
    DATABASE_URL: str = "sqlite:///./data/jianzao.db"

    # 安全配置
    SECRET_KEY: str = "jianzao-report-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    ALGORITHM: str = "HS256"

    # 文件上传
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # 飞书配置（税检康线索写入多维表）
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_BITABLE_APP_TOKEN: str = ""
    FEISHU_BITABLE_TABLE_ID: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
