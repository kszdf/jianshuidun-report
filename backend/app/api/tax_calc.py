"""
税务计算API - v0.2.0 新增
挂靠税费计算器、先扣后返、税率比价、混合销售平衡点
"""
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from decimal import Decimal

from app.core.database import get_db
from app.core.security import get_current_company_id
from app.services.tax_calc_service import (
    calculate_affiliated_tax,
    calculate_pre_deduct_return,
    calculate_tax_rate_comparison,
    calculate_mixed_sales_break_even,
)
from app.services.project_accounting_service import (
    get_lmr_reference,
    compare_lmr_with_reference,
)

router = APIRouter()


# ============================================================
# 挂靠税费计算器
# ============================================================

class AffiliatedTaxParams(BaseModel):
    contract_amount: float = 1000000  # 合同金额（含税）
    tax_rate: float = 9.0  # 适用税率%
    management_fee_ratio: float = 2.0  # 挂靠费比例%
    vat_burden_rate: float = 2.5  # 增值税税负率%
    income_tax_burden_rate: float = 1.5  # 所得税税负率%


@router.post("/affiliated-tax", summary="挂靠税费精算计算器")
def affiliated_tax_calculator(
    params: AffiliatedTaxParams,
    company_id: int = Depends(get_current_company_id),
):
    """挂靠税费精算计算器 - 输入5个核心变量，输出各项税费明细"""
    result = calculate_affiliated_tax(params.dict())
    return result


# ============================================================
# 先扣后返模式
# ============================================================

class PreDeductReturnParams(AffiliatedTaxParams):
    provided_input_tax: float = 0  # 已提供进项税额
    provided_cost_invoice: float = 0  # 已提供成本发票金额（不含税）


@router.post("/pre-deduct-return", summary="先扣后返模式计算")
def pre_deduct_return_calculator(
    params: PreDeductReturnParams,
    company_id: int = Depends(get_current_company_id),
):
    """先扣后返模式 - 先全额扣除，再根据提供的发票计算返还"""
    result = calculate_pre_deduct_return(params.dict())
    return result


# ============================================================
# 税率变动比价器
# ============================================================

class TaxRateComparisonParams(BaseModel):
    amount: float = 1000000  # 金额
    amount_type: str = "with_tax"  # 金额类型：with_tax含税 / no_tax不含税
    old_rate: float = 13.0  # 旧税率%
    new_rate: float = 9.0  # 新税率%


@router.post("/tax-rate-comparison", summary="税率变动比价器")
def tax_rate_comparison(
    params: TaxRateComparisonParams,
    company_id: int = Depends(get_current_company_id),
):
    """税率变动比价器 - 对比两个税率下的不含税金额、税额、价税合计变化"""
    result = calculate_tax_rate_comparison(params.dict())
    return result


# ============================================================
# 混合销售平衡点测算
# ============================================================

class MixedSalesBreakEvenParams(BaseModel):
    goods_amount: float = 500000  # 货物金额（含税）
    install_amount: float = 500000  # 安装金额（含税）
    goods_rate: float = 13.0  # 货物税率%
    install_rate: float = 9.0  # 安装税率%
    mixed_rate: float = 13.0  # 混合销售税率%（从高适用）


@router.post("/mixed-sales-break-even", summary="混合销售平衡点测算")
def mixed_sales_break_even(
    params: MixedSalesBreakEvenParams,
    company_id: int = Depends(get_current_company_id),
):
    """混合销售平衡点测算 - 货物+安装，分开签vs合并签的税负差异"""
    result = calculate_mixed_sales_break_even(params.dict())
    return result


# ============================================================
# 人材机占比参考库
# ============================================================

@router.get("/lmr-reference", summary="人材机占比参考库")
def lmr_reference(
    company_id: int = Depends(get_current_company_id),
):
    """获取7类工程的人材机占比参考值"""
    return {"items": get_lmr_reference()}


@router.post("/lmr-compare", summary="人材机占比对比")
def lmr_compare(
    project_type: str = Body(..., description="工程类型"),
    cost_structure: list = Body(..., description="项目成本结构"),
    company_id: int = Depends(get_current_company_id),
):
    """对比项目人材机占比与行业参考值的差异"""
    result = compare_lmr_with_reference(cost_structure, project_type)
    return result
