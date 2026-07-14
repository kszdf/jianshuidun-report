"""
数据模型 - 配置（科目映射、标准科目）
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Integer, Numeric, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base


class CfgStdSubject(Base):
    """标准科目表 - 建筑行业预置"""
    __tablename__ = "cfg_std_subject"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=0, index=True, comment="公司ID，0=系统预置")
    subject_code = Column(String(20), index=True, comment="标准科目编码")
    subject_name = Column(String(100), comment="标准科目名称")
    parent_code = Column(String(20), comment="上级科目编码")
    subject_type = Column(String(20), index=True, comment="科目类型：income/cost/expense/asset/liability/equity")
    report_category = Column(String(50), index=True, comment="报表分类")
    level = Column(Integer, default=1, comment="科目级次")
    sort_order = Column(Integer, default=0, comment="排序号")
    is_leaf = Column(Boolean, default=True, comment="是否末级")


class CfgSubjectMapping(Base):
    """企业科目映射表"""
    __tablename__ = "cfg_subject_mapping"
    __table_args__ = (
        Index("idx_company_source", "company_id", "source_code", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    source_code = Column(String(50), comment="企业科目编码")
    source_name = Column(String(200), comment="企业科目名称")
    source_full_name = Column(String(500), comment="企业科目全称")
    std_subject_id = Column(Integer, nullable=True, comment="映射的标准科目ID")
    std_subject_code = Column(String(20), nullable=True, comment="标准科目编码")
    std_subject_name = Column(String(100), nullable=True, comment="标准科目名称")
    match_type = Column(String(20), default="auto", comment="匹配方式：auto/manual")
    match_confidence = Column(Numeric(5, 2), default=0, comment="匹配置信度")
    is_mapped = Column(Boolean, default=False, comment="是否已映射")
    remark = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
