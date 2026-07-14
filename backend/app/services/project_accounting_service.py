"""
项目独立核算服务 - v0.2.0 新增
核心功能：项目列表看板、单项目详情（收入/成本/毛利/资金/发票）
支持三种收入确认模式切换
"""
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from app.models.finance import AccSubjectBalance, AccVoucherItem, AccVoucher
from app.models.business import BizProject, BizCustomer
from app.models.business_ext import BizProjectAccounting
from app.models.config import CfgSubjectMapping, CfgStdSubject


def _to_float(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def _round2(val):
    if isinstance(val, Decimal):
        return float(val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    return round(float(val), 2)


# ============================================================
# 三种收入确认模式
# ============================================================

def _get_income_by_mode(db: Session, company_id: int, project_name: str,
                        mode: str = 'invoicing', period: str = None,
                        completion_percent: float = None,
                        estimated_total_income: float = None) -> dict:
    """
    按指定模式计算项目收入
    
    mode: 
        - invoicing: 开票口径（按开票金额确认收入，最常用）
        - settlement: 结算口径（按工程结算贷方发生额确认收入）
        - percentage: 完工百分比法（完工比例由用户手动输入）
    """
    result = {
        "mode": mode,
        "mode_name": {
            "invoicing": "开票口径",
            "settlement": "结算口径", 
            "percentage": "完工百分比法"
        }.get(mode, "开票口径"),
        "income_amount": 0.0,
        "income_no_tax": 0.0,
        "detail": {},
    }

    if mode == 'invoicing':
        # 开票口径：从销项发票数据获取（MVP简化：用主营业务收入的项目辅助核算）
        # 实际场景应该从发票表取数，这里先用收入科目贷方发生额模拟
        income_codes = _get_std_subject_codes(db, company_id, "income_main")
        if not income_codes:
            income_codes = _get_std_subject_codes(db, company_id, "income")
        
        amount = _get_voucher_sum_by_project(db, company_id, income_codes, project_name, "credit", period)
        result["income_amount"] = _round2(amount)
        result["income_no_tax"] = _round2(amount / 1.09)  # 假设9%税率
        result["detail"]["description"] = "按开票金额确认收入（主营业务收入贷方发生额）"

    elif mode == 'settlement':
        # 结算口径：工程结算贷方发生额
        # 注意：工程结算是成本类备抵科目，不是收入类
        # 正确做法是取工程结算(5402)的贷方发生额
        settlement_codes = _get_std_subject_codes_by_name(db, company_id, ["工程结算", "5402"])
        
        amount = _get_voucher_sum_by_project(db, company_id, settlement_codes, project_name, "credit", period)
        result["income_amount"] = _round2(amount)
        result["income_no_tax"] = _round2(amount / 1.09)
        result["detail"]["description"] = "按工程结算贷方发生额确认收入"

    elif mode == 'percentage':
        # 完工百分比法：合同总收入 × 完工百分比
        if estimated_total_income and completion_percent:
            total_income = float(estimated_total_income)
            percent = float(completion_percent) / 100
            amount = total_income * percent
            result["income_amount"] = _round2(amount)
            result["income_no_tax"] = _round2(amount / 1.09)
            result["detail"]["completion_percent"] = completion_percent
            result["detail"]["estimated_total_income"] = estimated_total_income
            result["detail"]["description"] = f"按完工百分比{completion_percent}%确认收入"

    return result


def _get_cost_by_income_ratio(db: Session, company_id: int, project_name: str,
                               income_amount: float, estimated_total_income: float = None,
                               estimated_total_cost: float = None, period: str = None) -> dict:
    """
    按收入匹配结转成本
    成本结转逻辑：按收入占预计总收入的比例结转成本
    """
    # 先获取已发生的成本（工程施工/合同履约成本借方发生额）
    cost_codes = _get_cost_subject_codes(db, company_id)
    incurred_cost = _get_voucher_sum_by_project(db, company_id, cost_codes, project_name, "debit", period)

    # 成本结构
    cost_structure = _get_project_cost_structure(db, company_id, project_name, period)

    # 按收入比例结转成本
    if estimated_total_income and estimated_total_cost and income_amount > 0:
        # 完工进度 = 收入 / 预计总收入
        progress = income_amount / estimated_total_income
        # 应结转成本 = 预计总成本 × 完工进度
        carryover_cost = estimated_total_cost * progress
        carryover_cost = min(carryover_cost, incurred_cost)  # 不超过实际发生
    else:
        # 没有预计数据时，按实际发生成本结转（不超过收入的85%作为合理毛利率）
        carryover_cost = min(incurred_cost, income_amount * 0.85)

    # 计算毛利
    gross_profit = income_amount - carryover_cost
    gross_profit_rate = (gross_profit / income_amount * 100) if income_amount > 0 else 0

    return {
        "incurred_cost": _round2(incurred_cost),  # 已发生成本
        "carryover_cost": _round2(carryover_cost),  # 结转成本（与收入匹配）
        "cost_structure": cost_structure,
        "gross_profit": _round2(gross_profit),
        "gross_profit_rate": _round2(gross_profit_rate),
    }


# ============================================================
# 项目列表看板
# ============================================================

def get_project_board_list(db: Session, company_id: int, 
                            income_mode: str = 'invoicing',
                            period: str = None) -> dict:
    """
    获取项目独立核算看板列表
    每个项目展示：项目名称、合同金额、已开票、已收款、已发生成本、毛利、毛利率、进度
    """
    # 获取所有项目
    projects = db.query(BizProject).filter(
        BizProject.company_id == company_id,
    ).order_by(BizProject.id).all()

    result_list = []
    total_contract = 0
    total_income = 0
    total_cost = 0
    total_profit = 0
    total_received = 0

    for proj in projects:
        proj_name = proj.project_name
        
        # 收入（按指定模式）
        income_result = _get_income_by_mode(
            db, company_id, proj_name, income_mode, period,
            None, _to_float(proj.contract_amount)
        )
        income_amount = income_result["income_amount"]

        # 成本与毛利
        cost_result = _get_cost_by_income_ratio(
            db, company_id, proj_name, income_amount,
            _to_float(proj.contract_amount), _to_float(proj.budget_cost),
            period
        )

        # 已收款（应收账款贷方 - 预收账款贷方，按项目汇总）
        received = _get_project_received(db, company_id, proj_name, period)

        # 进度计算
        contract_amount = _to_float(proj.contract_amount)
        progress = (income_amount / contract_amount * 100) if contract_amount > 0 else 0

        item = {
            "project_id": proj.id,
            "project_name": proj.project_name,
            "project_code": proj.project_code,
            "status": proj.status,
            "contract_amount": _round2(contract_amount),
            "income_amount": income_amount,
            "income_mode": income_mode,
            "received_amount": _round2(received),
            "pending_receive": _round2(income_amount - received),
            "incurred_cost": cost_result["incurred_cost"],
            "carryover_cost": cost_result["carryover_cost"],
            "gross_profit": cost_result["gross_profit"],
            "gross_profit_rate": cost_result["gross_profit_rate"],
            "progress": _round2(progress),
            "manager": proj.manager,
        }
        result_list.append(item)

        total_contract += contract_amount
        total_income += income_amount
        total_cost += cost_result["carryover_cost"]
        total_profit += cost_result["gross_profit"]
        total_received += received

    return {
        "total": len(result_list),
        "items": result_list,
        "summary": {
            "total_contract": _round2(total_contract),
            "total_income": _round2(total_income),
            "total_cost": _round2(total_cost),
            "total_profit": _round2(total_profit),
            "total_received": _round2(total_received),
            "overall_profit_rate": _round2((total_profit / total_income * 100) if total_income > 0 else 0),
        }
    }


# ============================================================
# 单项目详情
# ============================================================

def get_project_detail(db: Session, company_id: int, project_id: int,
                       income_mode: str = 'invoicing',
                       completion_percent: float = None,
                       period: str = None) -> dict:
    """
    获取单个项目的详细核算数据
    包含：收入情况、成本明细、毛利分析、资金情况、发票情况
    """
    proj = db.query(BizProject).filter(
        BizProject.company_id == company_id,
        BizProject.id == project_id,
    ).first()

    if not proj:
        return {"error": "项目不存在"}

    proj_name = proj.project_name
    contract_amount = _to_float(proj.contract_amount)
    budget_cost = _to_float(proj.budget_cost)

    # 1. 收入情况（三种模式都算出来，前端切换展示）
    income_modes = {}
    for mode in ['invoicing', 'settlement', 'percentage']:
        income_modes[mode] = _get_income_by_mode(
            db, company_id, proj_name, mode, period,
            completion_percent, contract_amount
        )

    current_income = income_modes.get(income_mode, income_modes['invoicing'])
    income_amount = current_income["income_amount"]

    # 2. 成本明细
    cost_result = _get_cost_by_income_ratio(
        db, company_id, proj_name, income_amount,
        contract_amount, budget_cost, period
    )

    # 3. 毛利分析
    gross_profit = cost_result["gross_profit"]
    gross_profit_rate = cost_result["gross_profit_rate"]

    # 4. 资金情况
    fund_info = _get_project_fund_info(db, company_id, proj_name, period)

    # 5. 发票情况
    invoice_info = _get_project_invoice_info(db, company_id, proj_name, period)

    # 6. 工程施工与工程结算对冲
    offset_info = _get_construction_settlement_offset(db, company_id, proj_name, period)

    return {
        "project_basic": {
            "project_id": proj.id,
            "project_name": proj.project_name,
            "project_code": proj.project_code,
            "customer_name": proj.customer_name,
            "contract_amount": _round2(contract_amount),
            "budget_cost": _round2(budget_cost),
            "status": proj.status,
            "manager": proj.manager,
            "start_date": str(proj.start_date) if proj.start_date else "",
            "end_date": str(proj.end_date) if proj.end_date else "",
        },
        "income_modes": income_modes,
        "current_mode": income_mode,
        "cost_detail": cost_result,
        "gross_profit": {
            "amount": gross_profit,
            "rate": gross_profit_rate,
            "expected_rate": _round2(((contract_amount - budget_cost) / contract_amount * 100) if contract_amount > 0 else 0),
        },
        "fund_info": fund_info,
        "invoice_info": invoice_info,
        "construction_settlement": offset_info,
    }


# ============================================================
# 资金情况
# ============================================================

def _get_project_fund_info(db: Session, company_id: int, project_name: str, period: str = None) -> dict:
    """获取项目资金情况：已收款/待收款/已付款/待付款"""
    # 已收款：应收账款贷方发生额 + 预收账款贷方发生额（按项目）
    received = _get_project_received(db, company_id, project_name, period)
    
    # 已付款：应付账款借方发生额 + 预付账款借方发生额（按项目）
    paid = _get_project_paid(db, company_id, project_name, period)

    # 待收款 = 应收账款余额（借方-贷方）
    ar_balance = _get_project_ar_balance(db, company_id, project_name, period)
    
    # 待付款 = 应付账款余额（贷方-借方）
    ap_balance = _get_project_ap_balance(db, company_id, project_name, period)

    return {
        "received_amount": _round2(received),  # 已收款
        "pending_receive": _round2(ar_balance),  # 待收款（应收余额）
        "paid_amount": _round2(paid),  # 已付款
        "pending_pay": _round2(ap_balance),  # 待付款（应付余额）
        "net_cash_flow": _round2(received - paid),  # 净现金流
    }


# ============================================================
# 发票情况（MVP简化版）
# ============================================================

def _get_project_invoice_info(db: Session, company_id: int, project_name: str, period: str = None) -> dict:
    """获取项目发票情况：销项/进项/缺票预警"""
    # 销项发票：从收入科目贷方发生额推算（含税）
    income_codes = _get_std_subject_codes(db, company_id, "income_main")
    if not income_codes:
        income_codes = _get_std_subject_codes(db, company_id, "income")
    output_amount_no_tax = _get_voucher_sum_by_project(db, company_id, income_codes, project_name, "credit", period)
    output_tax = output_amount_no_tax * 0.09
    output_amount_with_tax = output_amount_no_tax + output_tax

    # 进项发票：从工程施工/成本科目借方发生额中可抵扣部分推算
    cost_codes = _get_cost_subject_codes(db, company_id)
    cost_amount = _get_voucher_sum_by_project(db, company_id, cost_codes, project_name, "debit", period)
    # 假设60%的成本可取得进项，综合税率约6%
    estimated_input_tax = cost_amount * 0.6 * 0.06
    input_amount_with_tax = cost_amount * 0.6 + estimated_input_tax

    # 缺票预警
    # 理论应取得进项 = 销项税 - 目标增值税（按2.5%税负）
    vat_burden = 0.025
    target_vat = output_amount_no_tax * vat_burden
    theoretical_input = output_tax - target_vat
    missing_input = max(0, theoretical_input - estimated_input_tax)

    # 税负率计算
    actual_vat = max(0, output_tax - estimated_input_tax)
    vat_burden_actual = (actual_vat / output_amount_no_tax * 100) if output_amount_no_tax > 0 else 0

    return {
        "output": {
            "amount_with_tax": _round2(output_amount_with_tax),
            "amount_no_tax": _round2(output_amount_no_tax),
            "tax": _round2(output_tax),
        },
        "input": {
            "estimated_amount_with_tax": _round2(input_amount_with_tax),
            "estimated_tax": _round2(estimated_input_tax),
        },
        "missing_invoice": {
            "missing_input_tax": _round2(missing_input),
            "theoretical_input": _round2(theoretical_input),
            "warning": missing_input > 0,
        },
        "tax_burden": {
            "vat_burden": _round2(vat_burden_actual),
            "industry_reference": 2.5,  # 行业参考值
            "is_high": vat_burden_actual > 3.5,
            "is_low": vat_burden_actual < 1.5,
        }
    }


# ============================================================
# 工程施工与工程结算对冲
# ============================================================

def _get_construction_settlement_offset(db: Session, company_id: int, project_name: str, period: str = None) -> dict:
    """
    工程施工与工程结算对冲逻辑
    - 工程施工（合同成本+合同毛利）：借方余额
    - 工程结算：贷方余额
    - 已完工未结算 = 工程施工 - 工程结算（正数，相当于存货）
    - 已结算未完工 = 工程结算 - 工程施工（正数，相当于预收）
    """
    # 工程施工余额
    construction_codes = _get_std_subject_codes_by_name(db, company_id, ["工程施工", "合同履约成本", "5401"])
    construction_debit = _get_voucher_sum_by_project(db, company_id, construction_codes, project_name, "debit", period)
    construction_credit = _get_voucher_sum_by_project(db, company_id, construction_codes, project_name, "credit", period)
    construction_balance = construction_debit - construction_credit

    # 工程结算余额
    settlement_codes = _get_std_subject_codes_by_name(db, company_id, ["工程结算", "5402"])
    settlement_debit = _get_voucher_sum_by_project(db, company_id, settlement_codes, project_name, "debit", period)
    settlement_credit = _get_voucher_sum_by_project(db, company_id, settlement_codes, project_name, "credit", period)
    settlement_balance = settlement_credit - settlement_debit  # 贷方余额为正

    # 对冲结果
    diff = construction_balance - settlement_balance
    if diff > 0:
        status = "已完工未结算"
        amount = diff
    else:
        status = "已结算未完工"
        amount = -diff

    return {
        "construction_balance": _round2(construction_balance),  # 工程施工余额（借方为正）
        "settlement_balance": _round2(settlement_balance),  # 工程结算余额（贷方为正）
        "offset_status": status,  # 对冲状态
        "offset_amount": _round2(amount),  # 对冲差额
    }


# ============================================================
# 辅助工具函数
# ============================================================

def _get_std_subject_codes(db: Session, company_id: int, report_category: str) -> list:
    """获取某报表分类下的所有企业科目编码"""
    mappings = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.is_mapped == True,
    ).all()

    std_subjects = db.query(CfgStdSubject).filter(
        or_(
            CfgStdSubject.company_id == 0,
            CfgStdSubject.company_id == company_id,
        ),
        CfgStdSubject.report_category == report_category,
    ).all()
    std_codes = {s.subject_code for s in std_subjects}

    result = set()
    for m in mappings:
        if m.std_subject_code and m.std_subject_code in std_codes:
            result.add(m.source_code)

    return list(result)


def _get_std_subject_codes_by_name(db: Session, company_id: int, keywords: list) -> list:
    """按科目名称或编码获取企业科目编码"""
    mappings = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.is_mapped == True,
    ).all()

    result = set()
    for m in mappings:
        # 匹配科目名称或编码
        for kw in keywords:
            if (m.source_name and kw in m.source_name) or (m.source_code and kw in m.source_code):
                result.add(m.source_code)
                break

    return list(result)


def _get_cost_subject_codes(db: Session, company_id: int) -> list:
    """获取成本类科目编码（工程施工/合同履约成本等）"""
    categories = ["cost", "cost_labor", "cost_material", "cost_machine", "cost_other"]
    codes = set()
    for cat in categories:
        cat_codes = _get_std_subject_codes(db, company_id, cat)
        codes.update(cat_codes)
    
    # 也包括工程施工/合同履约成本等存货类科目
    inventory_codes = _get_std_subject_codes(db, company_id, "asset_inventory")
    # 过滤：只取包含"工程施工"、"合同履约成本"、"机械作业"的
    mappings = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.is_mapped == True,
        CfgSubjectMapping.source_code.in_(list(inventory_codes)) if inventory_codes else True,
    ).all()
    for m in mappings:
        if m.source_name and any(kw in m.source_name for kw in ["工程施工", "合同履约", "机械作业", "施工"]):
            codes.add(m.source_code)

    return list(codes)


def _get_voucher_sum_by_project(db: Session, company_id: int, subject_codes: list,
                                 project_name: str, amount_field: str, period: str = None) -> float:
    """按项目汇总凭证发生额"""
    if not subject_codes:
        return 0.0

    query = db.query(
        func.sum(getattr(AccVoucherItem, amount_field)).label("total")
    ).filter(
        AccVoucherItem.company_id == company_id,
        AccVoucherItem.std_subject_code.in_(subject_codes),
        AccVoucherItem.aux_project == project_name,
    )

    if period:
        query = query.filter(AccVoucherItem.period == period)

    row = query.first()
    return _to_float(row[0]) if row and row[0] else 0.0


def _get_project_cost_structure(db: Session, company_id: int, project_name: str, period: str = None) -> list:
    """项目成本结构分析（人材机分包其他）"""
    categories = [
        ("cost_labor", "人工费"),
        ("cost_material", "材料费"),
        ("cost_machine", "机械费"),
        ("cost_other", "其他费用"),
    ]

    # 也可以从凭证明细中按科目名称关键字分类
    # 这里简化：先按标准科目分类取数
    result = []
    total = 0

    for cat_code, cat_name in categories:
        codes = _get_std_subject_codes(db, company_id, cat_code)
        if not codes:
            continue
        amount = _get_voucher_sum_by_project(db, company_id, codes, project_name, "debit", period)
        if amount > 0:
            result.append({"name": cat_name, "value": _round2(amount)})
            total += amount

    # 如果分类数据为空，用工程施工总额拆分为一个"工程施工"项
    if total == 0:
        cost_codes = _get_cost_subject_codes(db, company_id)
        total_cost = _get_voucher_sum_by_project(db, company_id, cost_codes, project_name, "debit", period)
        if total_cost > 0:
            # 按行业参考比例拆分（房建：人工30% 材料60% 机械10%）
            result = [
                {"name": "人工费", "value": _round2(total_cost * 0.3)},
                {"name": "材料费", "value": _round2(total_cost * 0.6)},
                {"name": "机械费", "value": _round2(total_cost * 0.1)},
            ]
            total = total_cost

    # 计算占比
    for item in result:
        item["ratio"] = _round2((item["value"] / total * 100) if total > 0 else 0)

    return result


def _get_project_received(db: Session, company_id: int, project_name: str, period: str = None) -> float:
    """获取项目已收款金额（应收账款贷方+预收账款贷方）"""
    ar_codes = _get_std_subject_codes(db, company_id, "asset_ar")
    pre_receive_codes = _get_std_subject_codes(db, company_id, "liability_pre_receive")
    all_codes = ar_codes + pre_receive_codes

    if not all_codes:
        return 0.0

    # 应收账款贷方（收回的款项）
    ar_credit = _get_voucher_sum_by_project(db, company_id, ar_codes, project_name, "credit", period)
    # 预收账款贷方（预收的款项）
    pre_credit = _get_voucher_sum_by_project(db, company_id, pre_receive_codes, project_name, "credit", period)

    return ar_credit + pre_credit


def _get_project_paid(db: Session, company_id: int, project_name: str, period: str = None) -> float:
    """获取项目已付款金额（应付账款借方+预付账款借方）"""
    ap_codes = _get_std_subject_codes(db, company_id, "liability_ap")
    pre_pay_codes = _get_std_subject_codes(db, company_id, "asset_pre_pay")

    # 应付账款借方（支付的款项）
    ap_debit = _get_voucher_sum_by_project(db, company_id, ap_codes, project_name, "debit", period)
    # 预付账款借方（预付的款项）
    pre_debit = _get_voucher_sum_by_project(db, company_id, pre_pay_codes, project_name, "debit", period)

    return ap_debit + pre_debit


def _get_project_ar_balance(db: Session, company_id: int, project_name: str, period: str = None) -> float:
    """获取项目应收账款余额"""
    ar_codes = _get_std_subject_codes(db, company_id, "asset_ar")
    pre_receive_codes = _get_std_subject_codes(db, company_id, "liability_pre_receive")

    # 应收借方 - 应收贷方 = 应收余额
    ar_debit = _get_voucher_sum_by_project(db, company_id, ar_codes, project_name, "debit", period)
    ar_credit = _get_voucher_sum_by_project(db, company_id, ar_codes, project_name, "credit", period)
    ar_balance = ar_debit - ar_credit

    # 预收贷方 - 预收借方 = 预收余额（作为应收减项）
    pre_credit = _get_voucher_sum_by_project(db, company_id, pre_receive_codes, project_name, "credit", period)
    pre_debit = _get_voucher_sum_by_project(db, company_id, pre_receive_codes, project_name, "debit", period)
    pre_balance = pre_credit - pre_debit

    return ar_balance - pre_balance


def _get_project_ap_balance(db: Session, company_id: int, project_name: str, period: str = None) -> float:
    """获取项目应付账款余额"""
    ap_codes = _get_std_subject_codes(db, company_id, "liability_ap")
    pre_pay_codes = _get_std_subject_codes(db, company_id, "asset_pre_pay")

    # 应付贷方 - 应付借方 = 应付余额
    ap_credit = _get_voucher_sum_by_project(db, company_id, ap_codes, project_name, "credit", period)
    ap_debit = _get_voucher_sum_by_project(db, company_id, ap_codes, project_name, "debit", period)
    ap_balance = ap_credit - ap_debit

    # 预付借方 - 预付贷方 = 预付余额（作为应付减项）
    pre_debit = _get_voucher_sum_by_project(db, company_id, pre_pay_codes, project_name, "debit", period)
    pre_credit = _get_voucher_sum_by_project(db, company_id, pre_pay_codes, project_name, "credit", period)
    pre_balance = pre_debit - pre_credit

    return ap_balance - pre_balance


# ============================================================
# 人材机占比参考库
# ============================================================

LMR_REFERENCE_DATA = [
    {"project_type": "房建工程", "labor_ratio": 30, "material_ratio": 60, "machine_ratio": 10,
     "description": "房屋建筑工程，人工占比较高，材料占比最大"},
    {"project_type": "市政工程", "labor_ratio": 20, "material_ratio": 55, "machine_ratio": 25,
     "description": "市政道路、桥梁等，机械占比较高"},
    {"project_type": "装修工程", "labor_ratio": 40, "material_ratio": 55, "machine_ratio": 5,
     "description": "装饰装修工程，人工占比最高"},
    {"project_type": "劳务工程", "labor_ratio": 95, "material_ratio": 3, "machine_ratio": 2,
     "description": "纯劳务分包，人工占绝对比重"},
    {"project_type": "安装工程", "labor_ratio": 50, "material_ratio": 40, "machine_ratio": 10,
     "description": "机电安装工程，人工材料各半"},
    {"project_type": "水利工程", "labor_ratio": 10, "material_ratio": 40, "machine_ratio": 50,
     "description": "水利水电工程，机械占比最高"},
    {"project_type": "园林工程", "labor_ratio": 40, "material_ratio": 50, "machine_ratio": 10,
     "description": "园林绿化工程，人工材料为主"},
]


def get_lmr_reference() -> list:
    """获取人材机占比参考库"""
    return LMR_REFERENCE_DATA


def compare_lmr_with_reference(project_cost_structure: list, project_type: str) -> dict:
    """
    对比项目人材机占比与行业参考值的差异
    project_cost_structure: [{"name": "人工费", "value": 100, "ratio": 30}, ...]
    project_type: 工程类型
    """
    ref = next((r for r in LMR_REFERENCE_DATA if r["project_type"] == project_type), None)
    if not ref:
        return {"error": "未找到对应工程类型的参考值"}

    # 将项目成本结构转换为字典
    project_ratios = {}
    for item in project_cost_structure:
        name = item["name"]
        if "人工" in name:
            project_ratios["labor"] = item["ratio"]
        elif "材料" in name:
            project_ratios["material"] = item["ratio"]
        elif "机械" in name:
            project_ratios["machine"] = item["ratio"]
        else:
            project_ratios["other"] = item["ratio"]

    comparison = [
        {
            "name": "人工费",
            "project_ratio": project_ratios.get("labor", 0),
            "reference_ratio": ref["labor_ratio"],
            "diff": round(project_ratios.get("labor", 0) - ref["labor_ratio"], 2),
        },
        {
            "name": "材料费",
            "project_ratio": project_ratios.get("material", 0),
            "reference_ratio": ref["material_ratio"],
            "diff": round(project_ratios.get("material", 0) - ref["material_ratio"], 2),
        },
        {
            "name": "机械费",
            "project_ratio": project_ratios.get("machine", 0),
            "reference_ratio": ref["machine_ratio"],
            "diff": round(project_ratios.get("machine", 0) - ref["machine_ratio"], 2),
        },
    ]

    return {
        "project_type": project_type,
        "reference": ref,
        "comparison": comparison,
    }
