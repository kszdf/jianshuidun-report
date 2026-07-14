"""
报表API
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_company_id
from app.services.report_service import (
    get_dashboard_data,
    get_project_profit_list,
    get_project_profit_detail,
    get_cash_daily_report,
    get_ar_aging_report,
)

router = APIRouter()


@router.get("/dashboard", summary="经营驾驶舱")
def dashboard(
    period: Optional[str] = Query(None, description="期间 YYYY-MM"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """获取经营驾驶舱数据：6个核心指标 + 趋势图 + 预警"""
    return get_dashboard_data(db, company_id, period)


@router.get("/project-profit", summary="项目利润表")
def project_profit(
    period: Optional[str] = Query(None, description="期间 YYYY-MM，不填则本年累计"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """项目利润表 - 按项目维度汇总收入成本利润"""
    data = get_project_profit_list(db, company_id, period)
    return {"total": len(data), "items": data}


@router.get("/project-profit/detail", summary="项目利润详情")
def project_profit_detail(
    project_name: str = Query(..., description="项目名称"),
    period: Optional[str] = Query(None, description="期间 YYYY-MM"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """单个项目的利润明细"""
    return get_project_profit_detail(db, company_id, project_name, period)


@router.get("/cash-daily", summary="资金日报表")
def cash_daily(
    report_date: Optional[str] = Query(None, description="报表日期 YYYY-MM-DD"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """资金日报表 - 各账户余额 + 当日收支"""
    return get_cash_daily_report(db, company_id, report_date)


@router.get("/ar-aging", summary="应收账龄表")
def ar_aging(
    period: Optional[str] = Query(None, description="期间 YYYY-MM"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """应收账龄分析表 - 按账龄段分布 + 客户明细"""
    return get_ar_aging_report(db, company_id, period)
