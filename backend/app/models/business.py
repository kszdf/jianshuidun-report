"""
数据模型 - 业务档案（项目、客户、供应商、银行账户）
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Integer, Numeric, Date
from sqlalchemy.sql import func
from app.core.database import Base


class BizProject(Base):
    """工程项目"""
    __tablename__ = "biz_project"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    project_code = Column(String(50), nullable=True, comment="项目编号")
    project_name = Column(String(200), index=True, comment="项目名称")
    customer_name = Column(String(200), nullable=True, comment="客户名称")
    contract_amount = Column(Numeric(18, 2), default=0, comment="合同金额")
    budget_cost = Column(Numeric(18, 2), default=0, comment="预算成本")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(String(20), default="ongoing", comment="状态：pending/ongoing/completed/settled")
    manager = Column(String(50), nullable=True, comment="项目经理")
    source = Column(String(20), default="auto", comment="来源：auto/manual")
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BizCustomer(Base):
    """客户档案"""
    __tablename__ = "biz_customer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    customer_code = Column(String(50), nullable=True)
    customer_name = Column(String(200), index=True)
    contact = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    source = Column(String(20), default="auto")
    created_at = Column(DateTime, server_default=func.now())


class BizSupplier(Base):
    """供应商档案"""
    __tablename__ = "biz_supplier"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    supplier_code = Column(String(50), nullable=True)
    supplier_name = Column(String(200), index=True)
    contact = Column(String(50), nullable=True)
    phone = Column(String(20), nullable=True)
    source = Column(String(20), default="auto")
    created_at = Column(DateTime, server_default=func.now())


class BizBankAccount(Base):
    """银行账户"""
    __tablename__ = "biz_bank_account"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    account_name = Column(String(100), comment="账户名称")
    bank_name = Column(String(100), comment="开户行")
    account_no = Column(String(50), comment="账号")
    account_type = Column(String(20), default="general", comment="类型：basic/general/private/cash")
    is_outer = Column(Boolean, default=False, comment="是否账外账户")
    current_balance = Column(Numeric(18, 2), default=0, comment="当前余额")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class AccCashflow(Base):
    """银行流水"""
    __tablename__ = "acc_cashflow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    batch_id = Column(Integer, nullable=True)
    account_id = Column(Integer, index=True)
    trans_date = Column(Date, index=True)
    summary = Column(String(500), nullable=True)
    income = Column(Numeric(18, 2), default=0)
    expense = Column(Numeric(18, 2), default=0)
    balance = Column(Numeric(18, 2), default=0)
    opposite_name = Column(String(200), nullable=True)
    opposite_account = Column(String(50), nullable=True)
    category = Column(String(50), nullable=True, comment="系统自动分类")
    category_manual = Column(String(50), nullable=True, comment="手工分类")
    related_project = Column(String(100), nullable=True)
    is_reconciled = Column(Boolean, default=False)
