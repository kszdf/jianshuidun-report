"""
数据模型 - 财务数据（凭证、余额、流水）
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Integer, Numeric, Date, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base


class ImpBatch(Base):
    """导入批次"""
    __tablename__ = "imp_batch"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    batch_no = Column(String(50), unique=True, comment="批次号")
    import_type = Column(String(30), comment="导入类型：balance/voucher/cashflow")
    source_file = Column(String(255), comment="源文件名")
    source_software = Column(String(50), comment="来源软件")
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    total_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)
    status = Column(String(20), default="importing", comment="状态")
    quality_score = Column(Integer, default=0, comment="数据质量评分")
    imported_by = Column(Integer, nullable=True)
    imported_at = Column(DateTime, server_default=func.now())
    remark = Column(Text, nullable=True)


class AccSubjectBalance(Base):
    """科目余额表"""
    __tablename__ = "acc_subject_balance"
    __table_args__ = (
        Index("idx_company_period", "company_id", "period"),
        Index("idx_company_std_code", "company_id", "std_subject_code"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    batch_id = Column(Integer, nullable=True)
    period = Column(String(7), index=True, comment="期间 YYYY-MM")
    subject_code = Column(String(50), comment="企业科目编码")
    subject_name = Column(String(200), comment="企业科目名称")
    subject_full_name = Column(String(500), comment="科目全称")
    std_subject_id = Column(Integer, nullable=True)
    std_subject_code = Column(String(20), nullable=True, index=True)
    begin_debit = Column(Numeric(18, 2), default=0)
    begin_credit = Column(Numeric(18, 2), default=0)
    current_debit = Column(Numeric(18, 2), default=0)
    current_credit = Column(Numeric(18, 2), default=0)
    end_debit = Column(Numeric(18, 2), default=0)
    end_credit = Column(Numeric(18, 2), default=0)
    year_debit = Column(Numeric(18, 2), default=0)
    year_credit = Column(Numeric(18, 2), default=0)
    aux_project = Column(String(100), nullable=True, comment="项目核算")
    aux_customer = Column(String(100), nullable=True, comment="客户核算")
    aux_supplier = Column(String(100), nullable=True, comment="供应商核算")
    has_aux = Column(Boolean, default=False)


class AccVoucher(Base):
    """凭证表"""
    __tablename__ = "acc_voucher"
    __table_args__ = (
        Index("idx_company_date", "company_id", "voucher_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    batch_id = Column(Integer, nullable=True)
    voucher_no = Column(String(50), comment="凭证号")
    voucher_date = Column(Date, index=True, comment="凭证日期")
    period = Column(String(7), index=True, comment="期间")
    summary = Column(String(500), comment="凭证摘要")
    total_debit = Column(Numeric(18, 2), default=0)
    total_credit = Column(Numeric(18, 2), default=0)
    auditor = Column(String(50), nullable=True)
    preparer = Column(String(50), nullable=True)
    is_posted = Column(Boolean, default=True)


class AccVoucherItem(Base):
    """凭证明细"""
    __tablename__ = "acc_voucher_item"
    __table_args__ = (
        Index("idx_company_std_date", "company_id", "std_subject_code", "voucher_date"),
        Index("idx_company_project", "company_id", "aux_project"),
        Index("idx_company_customer", "company_id", "aux_customer"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    voucher_id = Column(Integer, index=True)
    voucher_date = Column(Date, index=True)
    period = Column(String(7), index=True)
    line_no = Column(Integer, default=0)
    subject_code = Column(String(50))
    subject_name = Column(String(200))
    std_subject_id = Column(Integer, nullable=True)
    std_subject_code = Column(String(20), nullable=True, index=True)
    summary = Column(String(500), nullable=True)
    debit = Column(Numeric(18, 2), default=0)
    credit = Column(Numeric(18, 2), default=0)
    aux_project = Column(String(100), nullable=True, index=True)
    aux_customer = Column(String(100), nullable=True, index=True)
    aux_supplier = Column(String(100), nullable=True)
    aux_employee = Column(String(50), nullable=True)
