"""
数据模型 - 系统管理
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class SysUser(Base):
    """系统用户"""
    __tablename__ = "sys_user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True, comment="公司ID")
    username = Column(String(50), unique=True, index=True, comment="登录名")
    password_hash = Column(String(255), comment="密码哈希")
    real_name = Column(String(50), comment="真实姓名")
    role = Column(String(20), default="finance", comment="角色：boss/finance/manager")
    email = Column(String(100), comment="邮箱")
    phone = Column(String(20), comment="手机号")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)


class SysCompany(Base):
    """公司信息"""
    __tablename__ = "sys_company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), comment="公司名称")
    tax_no = Column(String(50), comment="税号")
    industry = Column(String(50), comment="行业")
    contact = Column(String(50), comment="联系人")
    phone = Column(String(20), comment="联系电话")
    created_at = Column(DateTime, server_default=func.now())
    expired_at = Column(DateTime, nullable=True, comment="到期时间")
