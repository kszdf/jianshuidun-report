"""
项目独立核算API - v0.2.0 新增
项目列表看板、单项目详情（收入/成本/毛利/资金/发票）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_company_id
from app.services.project_accounting_service import (
    get_project_board_list,
    get_project_detail,
)

router = APIRouter()


@router.get("/board", summary="项目独立核算看板列表")
def project_board(
    income_mode: str = Query("invoicing", description="收入确认模式：invoicing开票口径/settlement结算口径/percentage完工百分比"),
    period: Optional[str] = Query(None, description="期间 YYYY-MM，不填则本年累计"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """
    项目独立核算看板列表
    - 每个项目展示：项目名称、合同金额、已开票、已收款、已发生成本、毛利、毛利率、进度
    - 支持三种收入确认模式切换
    """
    result = get_project_board_list(db, company_id, income_mode, period)
    return result


@router.get("/detail", summary="单项目详情")
def project_detail(
    project_id: int = Query(..., description="项目ID"),
    income_mode: str = Query("invoicing", description="收入确认模式"),
    completion_percent: Optional[float] = Query(None, description="完工百分比（仅percentage模式有效）"),
    period: Optional[str] = Query(None, description="期间 YYYY-MM"),
    company_id: int = Depends(get_current_company_id),
    db: Session = Depends(get_db),
):
    """
    单个项目详细核算数据
    包含：收入情况（三模式）、成本明细、毛利分析、资金情况、发票情况、工程施工与结算对冲
    """
    result = get_project_detail(db, company_id, project_id, income_mode, completion_percent, period)
    return result
