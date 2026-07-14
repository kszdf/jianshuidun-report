"""
数据模型 - 业务扩展（项目核算、现金流预测、发票等）
v0.2.0 新增模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Integer, Numeric, Date, Text, Float, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base


class BizProjectAccounting(Base):
    """项目独立核算表 - 每个项目的核心指标汇总"""
    __tablename__ = "biz_project_accounting"
    __table_args__ = (
        Index("idx_pac_company_project", "company_id", "project_id", unique=True),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    project_id = Column(Integer, index=True, comment="项目ID")
    project_name = Column(String(200), comment="项目名称")

    # 合同信息
    contract_amount = Column(Numeric(18, 2), default=0, comment="合同金额（含税）")
    contract_amount_no_tax = Column(Numeric(18, 2), default=0, comment="合同金额（不含税）")
    tax_rate = Column(Numeric(5, 2), default=9.00, comment="适用税率%")

    # 收入情况（三种口径）
    invoiced_amount = Column(Numeric(18, 2), default=0, comment="已开票金额（含税）- 开票口径收入")
    settlement_amount = Column(Numeric(18, 2), default=0, comment="工程结算金额 - 结算口径收入")
    completion_percent = Column(Numeric(5, 2), default=0, comment="完工百分比% - 完工百分比法")
    estimated_total_income = Column(Numeric(18, 2), default=0, comment="预计总收入（不含税）")

    # 成本情况
    incurred_cost = Column(Numeric(18, 2), default=0, comment="已发生成本（工程施工借方）")
    labor_cost = Column(Numeric(18, 2), default=0, comment="人工费")
    material_cost = Column(Numeric(18, 2), default=0, comment="材料费")
    machine_cost = Column(Numeric(18, 2), default=0, comment="机械费")
    subcontract_cost = Column(Numeric(18, 2), default=0, comment="分包费")
    other_cost = Column(Numeric(18, 2), default=0, comment="其他费用")
    estimated_total_cost = Column(Numeric(18, 2), default=0, comment="预计总成本")

    # 资金情况
    received_amount = Column(Numeric(18, 2), default=0, comment="已收款金额")
    pending_receive = Column(Numeric(18, 2), default=0, comment="待收款金额")
    paid_amount = Column(Numeric(18, 2), default=0, comment="已付款金额")
    pending_pay = Column(Numeric(18, 2), default=0, comment="待付款金额")

    # 发票情况
    output_invoice_amount = Column(Numeric(18, 2), default=0, comment="销项发票金额（含税）")
    output_tax = Column(Numeric(18, 2), default=0, comment="销项税额")
    input_invoice_amount = Column(Numeric(18, 2), default=0, comment="进项发票金额（含税）")
    input_tax = Column(Numeric(18, 2), default=0, comment="进项税额")

    # 毛利
    gross_profit = Column(Numeric(18, 2), default=0, comment="毛利额")
    gross_profit_rate = Column(Numeric(5, 2), default=0, comment="毛利率%")

    # 工程施工与工程结算对冲
    construction_in_progress = Column(Numeric(18, 2), default=0, comment="工程施工余额（合同成本+合同毛利）")
    project_settlement = Column(Numeric(18, 2), default=0, comment="工程结算余额")

    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BizCashflowForecast(Base):
    """现金流预测表"""
    __tablename__ = "biz_cashflow_forecast"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    forecast_name = Column(String(200), comment="预测名称")
    start_month = Column(String(7), comment="起始月份 YYYY-MM")
    months_count = Column(Integer, default=3, comment="预测月数")
    safety_line = Column(Numeric(18, 2), default=0, comment="资金安全线")

    # 期初资金（按账户）
    opening_balance = Column(Numeric(18, 2), default=0, comment="期初可动用资金")
    frozen_balance = Column(Numeric(18, 2), default=0, comment="不可动用资金（保证金等）")

    # 收支明细存在明细表里
    status = Column(String(20), default="draft", comment="状态：draft/active/archived")
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class BizCashflowForecastItem(Base):
    """现金流预测明细表"""
    __tablename__ = "biz_cashflow_forecast_item"
    __table_args__ = (
        Index("idx_forecast_id", "forecast_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_id = Column(Integer, index=True)
    item_type = Column(String(20), comment="类型：income/expense")
    category = Column(String(50), comment="类别：工程款/材料款/人工费/机械费/分包款/税费/管理费/其他")
    item_name = Column(String(200), comment="项目名称")
    amount = Column(Numeric(18, 2), default=0, comment="金额")
    month = Column(String(7), comment="月份 YYYY-MM")
    related_project = Column(String(200), nullable=True, comment="关联项目")
    remark = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class RefLaborMaterialMachine(Base):
    """人材机占比参考库"""
    __tablename__ = "ref_labor_material_machine"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_type = Column(String(50), unique=True, comment="工程类型")
    labor_ratio = Column(Numeric(5, 2), default=0, comment="人工占比%")
    material_ratio = Column(Numeric(5, 2), default=0, comment="材料占比%")
    machine_ratio = Column(Numeric(5, 2), default=0, comment="机械占比%")
    description = Column(String(500), nullable=True, comment="说明")
    is_system = Column(Boolean, default=True, comment="是否系统内置")
    sort_order = Column(Integer, default=0)


class BizInvoiceSummary(Base):
    """发票汇总表"""
    __tablename__ = "biz_invoice_summary"
    __table_args__ = (
        Index("idx_bis_company_period", "company_id", "period"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, default=1, index=True)
    period = Column(String(7), comment="期间 YYYY-MM")
    invoice_type = Column(String(20), comment="类型：output销项/input进项")

    total_amount = Column(Numeric(18, 2), default=0, comment="金额合计（不含税）")
    total_tax = Column(Numeric(18, 2), default=0, comment="税额合计")
    total_price = Column(Numeric(18, 2), default=0, comment="价税合计")
    invoice_count = Column(Integer, default=0, comment="发票份数")

    # 按税率分布（JSON格式）
    tax_rate_breakdown = Column(JSON, nullable=True, comment="按税率分布明细")

    created_at = Column(DateTime, server_default=func.now())
