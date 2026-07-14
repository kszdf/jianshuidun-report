"""
报表计算服务 - 核心业务逻辑
所有报表的数据计算都在这里
"""
from sqlalchemy import func, and_, or_, case
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, date, timedelta

from app.models.finance import AccSubjectBalance, AccVoucherItem, AccVoucher
from app.models.business import BizProject, BizCustomer, BizBankAccount, AccCashflow
from app.models.config import CfgSubjectMapping, CfgStdSubject


# ============================================================
# 工具函数
# ============================================================

def _get_period_range(period: str = None) -> tuple:
    """获取期间范围，返回(开始期间, 结束期间)"""
    if not period:
        today = date.today()
        period = today.strftime("%Y-%m")
    return period


def _to_float(val) -> float:
    """Decimal转float，用于前端展示"""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


# ============================================================
# 驾驶舱
# ============================================================

def get_dashboard_data(db: Session, company_id: int, period: str = None) -> dict:
    """获取驾驶舱数据
    6个核心指标 + 2张趋势图 + 预警
    """
    if not period:
        today = date.today()
        period = today.strftime("%Y-%m")

    # 计算今年和去年同期
    current_year = period[:4]
    last_year = str(int(current_year) - 1)
    year_start = f"{current_year}-01"

    result = {
        "period": period,
        "indicators": _get_dashboard_indicators(db, company_id, period, current_year, last_year),
        "trends": _get_dashboard_trends(db, company_id, current_year),
        "warnings": _get_dashboard_warnings(db, company_id, period),
    }
    return result


def _get_dashboard_indicators(db: Session, company_id: int, period: str,
                               current_year: str, last_year: str) -> dict:
    """6个核心指标"""
    # 1. 在手资金 = 现金 + 银行存款 + 其他货币资金 期末余额
    cash_balance = _get_subject_end_balance(db, company_id, period, ["asset_cash"])

    # 2. 应收账款净额 = 应收 - 预收
    ar_balance = _get_subject_end_balance(db, company_id, period, ["asset_ar"])
    pre_receive = _get_subject_end_balance(db, company_id, period, ["liability_pre_receive"])
    ar_net = cash_balance  # placeholder
    ar_net = ar_balance - pre_receive

    # 3. 应付账款净额 = 应付 - 预付
    ap_balance = _get_subject_end_balance(db, company_id, period, ["liability_ap"])
    pre_pay = _get_subject_end_balance(db, company_id, period, ["asset_pre_pay"])
    ap_net = ap_balance - pre_pay

    # 4. 本月收入
    month_income = _get_period_income(db, company_id, period)
    last_month = _get_last_month(period)
    last_month_income = _get_period_income(db, company_id, last_month)
    income_mom = _calc_mom(month_income, last_month_income)

    # 5. 本月成本
    month_cost = _get_period_cost(db, company_id, period)
    last_month_cost = _get_period_cost(db, company_id, last_month)
    cost_mom = _calc_mom(month_cost, last_month_cost)

    # 6. 本月利润
    month_profit = month_income - month_cost
    profit_rate = (month_profit / month_income * 100) if month_income > 0 else 0

    # 在手项目数
    project_count = db.query(BizProject).filter(
        BizProject.company_id == company_id,
        BizProject.status == "ongoing"
    ).count()

    return [
        {"key": "cash", "name": "在手资金", "value": round(cash_balance, 2), "unit": "元",
         "trend": 0, "trend_type": "up"},
        {"key": "ar", "name": "应收账款", "value": round(ar_net, 2), "unit": "元",
         "trend": 0, "trend_type": "up"},
        {"key": "ap", "name": "应付账款", "value": round(ap_net, 2), "unit": "元",
         "trend": 0, "trend_type": "up"},
        {"key": "income", "name": "本月收入", "value": round(month_income, 2), "unit": "元",
         "trend": round(income_mom, 1), "trend_type": "up" if income_mom >= 0 else "down"},
        {"key": "cost", "name": "本月成本", "value": round(month_cost, 2), "unit": "元",
         "trend": round(cost_mom, 1), "trend_type": "up" if cost_mom >= 0 else "down"},
        {"key": "profit", "name": "本月利润", "value": round(month_profit, 2), "unit": "元",
         "trend": round(profit_rate, 1), "trend_type": "up" if profit_rate >= 0 else "down",
         "suffix": f"利润率 {profit_rate:.1f}%"},
        {"key": "projects", "name": "在手项目", "value": project_count, "unit": "个",
         "trend": 0, "trend_type": "up"},
    ]


def _get_dashboard_trends(db: Session, company_id: int, year: str) -> dict:
    """趋势数据：近6个月收支趋势 + 项目利润排行TOP5"""
    # 月度收支趋势（近6个月）
    income_trend = []
    cost_trend = []
    months = _get_last_n_months(6)

    for m in months:
        income = _get_period_income(db, company_id, m)
        cost = _get_period_cost(db, company_id, m)
        income_trend.append({"month": m, "value": round(income, 2)})
        cost_trend.append({"month": m, "value": round(cost, 2)})

    # 项目利润排行 TOP5
    project_profit = get_project_profit_list(db, company_id)
    top5 = sorted(project_profit, key=lambda x: x["profit"], reverse=True)[:5]

    # 应收账龄分布
    ar_aging = _get_ar_aging_distribution(db, company_id)

    return {
        "income_cost": {
            "months": months,
            "income": [item["value"] for item in income_trend],
            "cost": [item["value"] for item in cost_trend],
        },
        "project_top5": top5,
        "ar_aging": ar_aging,
    }


def _get_dashboard_warnings(db: Session, company_id: int, period: str) -> list:
    """预警列表 TOP5"""
    warnings = []

    # 1. 应收超期（90天以上）
    ar_aging = _get_ar_aging_detail(db, company_id)
    overdue_90 = [x for x in ar_aging if x["days"] > 90]
    if overdue_90:
        total_overdue = sum(x["balance"] for x in overdue_90)
        warnings.append({
            "level": "danger",
            "type": "应收超期",
            "message": f"{len(overdue_90)}家客户应收超90天，涉及金额 {total_overdue:,.2f} 元",
            "count": len(overdue_90),
        })

    # 2. 亏损项目
    projects = get_project_profit_list(db, company_id)
    loss_projects = [p for p in projects if p["profit"] < 0]
    if loss_projects:
        warnings.append({
            "level": "danger",
            "type": "亏损项目",
            "message": f"{len(loss_projects)}个项目亏损，亏损总额 {sum(p['profit'] for p in loss_projects):,.2f} 元",
            "count": len(loss_projects),
        })

    # 3. 资金紧张
    cash = _get_subject_end_balance(db, company_id, period, ["asset_cash"])
    month_cost = _get_period_cost(db, company_id, period)
    if month_cost > 0 and cash < month_cost * 0.5:
        warnings.append({
            "level": "warning",
            "type": "资金紧张",
            "message": f"在手资金不足半月支出，建议关注现金流",
            "count": 1,
        })

    return warnings[:5]


# ============================================================
# 项目利润表
# ============================================================

def get_project_profit_list(db: Session, company_id: int, period: str = None) -> list:
    """项目利润表 - 按项目维度汇总收入成本利润"""
    # 从凭证明细中，按项目辅助核算汇总收入类和成本类科目
    # 收入类科目：贷方发生额
    income_by_project = _get_voucher_sum_by_aux(
        db, company_id, "income", "aux_project", "credit", period
    )
    # 成本类科目：借方发生额
    cost_by_project = _get_voucher_sum_by_aux(
        db, company_id, "cost", "aux_project", "debit", period
    )

    # 合并项目列表
    all_projects = set(list(income_by_project.keys()) + list(cost_by_project.keys()))
    # 过滤掉空项目
    all_projects = [p for p in all_projects if p and p.strip()]

    result = []
    for proj_name in all_projects:
        income = income_by_project.get(proj_name, 0)
        cost = cost_by_project.get(proj_name, 0)
        profit = income - cost
        profit_rate = (profit / income * 100) if income > 0 else 0

        # 获取项目信息
        proj = db.query(BizProject).filter(
            BizProject.company_id == company_id,
            BizProject.project_name == proj_name
        ).first()

        result.append({
            "project_name": proj_name,
            "contract_amount": _to_float(proj.contract_amount) if proj else 0,
            "income": round(income, 2),
            "cost": round(cost, 2),
            "profit": round(profit, 2),
            "profit_rate": round(profit_rate, 1),
            "status": proj.status if proj else "unknown",
        })

    return sorted(result, key=lambda x: x["profit"], reverse=True)


def get_project_profit_detail(db: Session, company_id: int, project_name: str, period: str = None) -> dict:
    """单个项目的利润详情"""
    # 收入明细
    income_items = _get_voucher_detail_by_aux(
        db, company_id, "income", "aux_project", project_name, "credit", period
    )
    # 成本明细
    cost_items = _get_voucher_detail_by_aux(
        db, company_id, "cost", "aux_project", project_name, "debit", period
    )

    total_income = sum(i["amount"] for i in income_items)
    total_cost = sum(i["amount"] for i in cost_items)
    profit = total_income - total_cost
    profit_rate = (profit / total_income * 100) if total_income > 0 else 0

    # 成本结构
    cost_structure = _get_cost_structure(db, company_id, project_name, period)

    return {
        "project_name": project_name,
        "total_income": round(total_income, 2),
        "total_cost": round(total_cost, 2),
        "profit": round(profit, 2),
        "profit_rate": round(profit_rate, 1),
        "income_items": income_items,
        "cost_items": cost_items,
        "cost_structure": cost_structure,
    }


# ============================================================
# 资金日报表
# ============================================================

def get_cash_daily_report(db: Session, company_id: int, report_date: str = None) -> dict:
    """资金日报表"""
    if not report_date:
        report_date = date.today().strftime("%Y-%m-%d")

    # 各账户余额（从科目余额表取期末数）
    period = report_date[:7]
    cash_balance = _get_subject_end_balance_by_detail(db, company_id, period, "asset_cash")

    # 当日收支（从凭证明细取）
    daily_income = _get_daily_cashflow(db, company_id, report_date, "income")
    daily_expense = _get_daily_cashflow(db, company_id, report_date, "expense")

    # 银行账户列表
    accounts = db.query(BizBankAccount).filter(
        BizBankAccount.company_id == company_id
    ).order_by(BizBankAccount.sort_order, BizBankAccount.id).all()

    account_list = []
    total_balance = 0
    for acc in accounts:
        bal = _to_float(acc.current_balance)
        total_balance += bal
        account_list.append({
            "id": acc.id,
            "account_name": acc.account_name,
            "bank_name": acc.bank_name,
            "account_no": acc.account_no,
            "account_type": acc.account_type,
            "is_outer": acc.is_outer,
            "balance": round(bal, 2),
        })

    # 如果没有配置账户，用科目余额兜底
    if not account_list:
        account_list.append({
            "id": 0,
            "account_name": "银行存款合计",
            "bank_name": "",
            "account_no": "",
            "account_type": "total",
            "is_outer": False,
            "balance": round(cash_balance, 2),
        })
        total_balance = cash_balance

    return {
        "report_date": report_date,
        "total_balance": round(total_balance, 2),
        "daily_income": round(daily_income, 2),
        "daily_expense": round(daily_expense, 2),
        "net_flow": round(daily_income - daily_expense, 2),
        "accounts": account_list,
    }


# ============================================================
# 应收账龄表
# ============================================================

def get_ar_aging_report(db: Session, company_id: int, period: str = None) -> dict:
    """应收账龄分析表"""
    aging_detail = _get_ar_aging_detail(db, company_id)

    # 汇总各账龄段
    buckets = {
        "within_30": 0,  # 30天内
        "between_30_90": 0,  # 30-90天
        "between_90_180": 0,  # 90-180天
        "over_180": 0,  # 180天以上
    }

    for item in aging_detail:
        days = item["days"]
        bal = item["balance"]
        if days <= 30:
            buckets["within_30"] += bal
        elif days <= 90:
            buckets["between_30_90"] += bal
        elif days <= 180:
            buckets["between_90_180"] += bal
        else:
            buckets["over_180"] += bal

    total = sum(buckets.values())
    overdue_total = buckets["between_90_180"] + buckets["over_180"]
    overdue_rate = (overdue_total / total * 100) if total > 0 else 0

    return {
        "total_ar": round(total, 2),
        "overdue_total": round(overdue_total, 2),
        "overdue_rate": round(overdue_rate, 1),
        "buckets": {k: round(v, 2) for k, v in buckets.items()},
        "details": sorted(aging_detail, key=lambda x: x["days"], reverse=True),
    }


def _get_ar_aging_detail(db: Session, company_id: int) -> list:
    """应收账龄明细 - 按客户分组"""
    # 简化版：从科目余额中取应收账款各客户余额
    # 账龄按最后一笔收款日期计算
    # MVP先用固定估算，后续完善

    # 从凭证明细取客户辅助核算的应收科目余额
    ar_subject_codes = _get_std_subject_codes(db, company_id, "asset_ar")
    pre_receive_codes = _get_std_subject_codes(db, company_id, "liability_pre_receive")

    # 应收借方 - 应收贷方 = 应收余额（按客户）
    result = []
    customer_balances = {}
    customer_last_payment = {}

    # 查询应收科目凭证，按客户汇总
    items = db.query(AccVoucherItem).filter(
        AccVoucherItem.company_id == company_id,
        AccVoucherItem.std_subject_code.in_(ar_subject_codes + pre_receive_codes),
        AccVoucherItem.aux_customer.isnot(None),
        AccVoucherItem.aux_customer != "",
    ).all()

    for item in items:
        customer = item.aux_customer
        if not customer:
            continue
        is_ar = item.std_subject_code in ar_subject_codes
        debit = _to_float(item.debit)
        credit = _to_float(item.credit)

        if customer not in customer_balances:
            customer_balances[customer] = 0
            customer_last_payment[customer] = None

        if is_ar:
            # 应收账款：借方增，贷方减
            customer_balances[customer] += debit - credit
        else:
            # 预收账款：贷方增，借方减（作为应收的减项）
            customer_balances[customer] -= (credit - debit)

        # 记录最后一次收款（贷方发生）
        if credit > 0 and item.voucher_date:
            if customer_last_payment[customer] is None or item.voucher_date > customer_last_payment[customer]:
                customer_last_payment[customer] = item.voucher_date

    today = date.today()
    for customer, balance in customer_balances.items():
        if balance <= 0:
            continue
        last_pay = customer_last_payment.get(customer)
        if last_pay:
            days = (today - last_pay).days
        else:
            days = 90  # 无收款记录默认90天

        result.append({
            "customer_name": customer,
            "balance": round(balance, 2),
            "days": days,
            "last_payment_date": last_pay.strftime("%Y-%m-%d") if last_pay else "",
            "aging_level": _get_aging_level(days),
        })

    return result


def _get_ar_aging_distribution(db: Session, company_id: int) -> dict:
    """应收账龄分布（饼图用）"""
    detail = _get_ar_aging_detail(db, company_id)
    buckets = {
        "30天以内": 0,
        "30-90天": 0,
        "90-180天": 0,
        "180天以上": 0,
    }
    for item in detail:
        days = item["days"]
        bal = item["balance"]
        if days <= 30:
            buckets["30天以内"] += bal
        elif days <= 90:
            buckets["30-90天"] += bal
        elif days <= 180:
            buckets["90-180天"] += bal
        else:
            buckets["180天以上"] += bal

    return [{"name": k, "value": round(v, 2)} for k, v in buckets.items() if v > 0]


# ============================================================
# 底层数据获取函数
# ============================================================

def _get_std_subject_codes(db: Session, company_id: int, report_category: str) -> list:
    """获取某报表分类下的所有标准科目编码"""
    mappings = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.is_mapped == True,
    ).all()

    # 从映射表中找属于该分类的企业科目
    std_subjects = db.query(CfgStdSubject).filter(
        or_(
            CfgStdSubject.company_id == 0,
            CfgStdSubject.company_id == company_id,
        ),
        CfgStdSubject.report_category == report_category,
    ).all()
    std_codes = {s.subject_code for s in std_subjects}

    # 收集所有子科目
    result = set()
    for m in mappings:
        if m.std_subject_code and m.std_subject_code in std_codes:
            result.add(m.source_code)

    return list(result)


def _get_subject_end_balance(db: Session, company_id: int, period: str,
                             report_categories: list) -> float:
    """获取指定报表分类的科目期末余额（借方-贷方）"""
    subject_codes = []
    for cat in report_categories:
        codes = _get_std_subject_codes(db, company_id, cat)
        subject_codes.extend(codes)

    if not subject_codes:
        return 0.0

    rows = db.query(
        func.sum(AccSubjectBalance.end_debit - AccSubjectBalance.end_credit).label("total")
    ).filter(
        AccSubjectBalance.company_id == company_id,
        AccSubjectBalance.period == period,
        AccSubjectBalance.subject_code.in_(subject_codes),
    ).first()

    return _to_float(rows[0]) if rows and rows[0] else 0.0


def _get_subject_end_balance_by_detail(db: Session, company_id: int, period: str, cat: str) -> float:
    """获取科目期末余额（详细版）"""
    return _get_subject_end_balance(db, company_id, period, [cat])


def _get_period_income(db: Session, company_id: int, period: str) -> float:
    """某期间收入总额（收入类科目贷方发生额）"""
    subject_codes = _get_std_subject_codes(db, company_id, "income_main")
    if not subject_codes:
        subject_codes = _get_std_subject_codes(db, company_id, "income")

    if not subject_codes:
        return 0.0

    row = db.query(
        func.sum(AccSubjectBalance.current_credit).label("total")
    ).filter(
        AccSubjectBalance.company_id == company_id,
        AccSubjectBalance.period == period,
        AccSubjectBalance.subject_code.in_(subject_codes),
    ).first()

    return _to_float(row[0]) if row and row[0] else 0.0


def _get_period_cost(db: Session, company_id: int, period: str) -> float:
    """某期间成本总额（成本类科目借方发生额）"""
    subject_codes = _get_std_subject_codes(db, company_id, "cost")
    if not subject_codes:
        return 0.0

    row = db.query(
        func.sum(AccSubjectBalance.current_debit).label("total")
    ).filter(
        AccSubjectBalance.company_id == company_id,
        AccSubjectBalance.period == period,
        AccSubjectBalance.subject_code.in_(subject_codes),
    ).first()

    return _to_float(row[0]) if row and row[0] else 0.0


def _get_voucher_sum_by_aux(db: Session, company_id: int, subject_type: str,
                            aux_field: str, amount_field: str, period: str = None) -> dict:
    """
    按辅助核算维度汇总凭证发生额
    subject_type: income/cost/expense
    aux_field: aux_project/aux_customer/aux_supplier
    amount_field: debit/credit
    """
    subject_codes = _get_std_subject_codes(db, company_id, subject_type)
    if not subject_codes:
        return {}

    query = db.query(
        getattr(AccVoucherItem, aux_field),
        func.sum(getattr(AccVoucherItem, amount_field)).label("total")
    ).filter(
        AccVoucherItem.company_id == company_id,
        AccVoucherItem.std_subject_code.in_(subject_codes),
    )

    if period:
        query = query.filter(AccVoucherItem.period == period)

    query = query.group_by(getattr(AccVoucherItem, aux_field))

    result = {}
    for row in query.all():
        key = row[0]
        if key:
            result[key] = _to_float(row[1])

    return result


def _get_voucher_detail_by_aux(db: Session, company_id: int, subject_type: str,
                               aux_field: str, aux_value: str,
                               amount_field: str, period: str = None) -> list:
    """按辅助核算取凭证明细"""
    subject_codes = _get_std_subject_codes(db, company_id, subject_type)
    if not subject_codes:
        return []

    query = db.query(AccVoucherItem, AccVoucher).join(
        AccVoucher, AccVoucherItem.voucher_id == AccVoucher.id
    ).filter(
        AccVoucherItem.company_id == company_id,
        AccVoucherItem.std_subject_code.in_(subject_codes),
        getattr(AccVoucherItem, aux_field) == aux_value,
    )

    if period:
        query = query.filter(AccVoucherItem.period == period)

    query = query.order_by(AccVoucher.voucher_date.desc())

    result = []
    for item, voucher in query.limit(100).all():
        result.append({
            "date": voucher.voucher_date.strftime("%Y-%m-%d") if voucher.voucher_date else "",
            "voucher_no": voucher.voucher_no,
            "summary": item.summary or voucher.summary,
            "subject_name": item.subject_name,
            "amount": _to_float(getattr(item, amount_field)),
        })

    return result


def _get_cost_structure(db: Session, company_id: int, project_name: str, period: str = None) -> list:
    """成本结构分析"""
    # 按成本子分类汇总
    categories = ["cost_labor", "cost_material", "cost_machine", "cost_other"]
    result = []

    for cat in categories:
        subject_codes = _get_std_subject_codes(db, company_id, cat)
        if not subject_codes:
            continue

        row = db.query(
            func.sum(AccVoucherItem.debit).label("total")
        ).filter(
            AccVoucherItem.company_id == company_id,
            AccVoucherItem.std_subject_code.in_(subject_codes),
            AccVoucherItem.aux_project == project_name,
        ).first()

        amount = _to_float(row[0]) if row and row[0] else 0
        if amount > 0:
            cat_name = {
                "cost_labor": "人工费",
                "cost_material": "材料费",
                "cost_machine": "机械费",
                "cost_other": "其他费用",
            }.get(cat, cat)
            result.append({"name": cat_name, "value": round(amount, 2)})

    return result


def _get_daily_cashflow(db: Session, company_id: int, report_date: str, direction: str) -> float:
    """当日资金流入/流出"""
    cash_codes = _get_std_subject_codes(db, company_id, "asset_cash")
    if not cash_codes:
        return 0.0

    date_obj = datetime.strptime(report_date, "%Y-%m-%d").date()

    if direction == "income":
        amount_col = AccVoucherItem.debit
    else:
        amount_col = AccVoucherItem.credit

    row = db.query(func.sum(amount_col)).filter(
        AccVoucherItem.company_id == company_id,
        AccVoucherItem.std_subject_code.in_(cash_codes),
        AccVoucherItem.voucher_date == date_obj,
    ).first()

    return _to_float(row[0]) if row and row[0] else 0.0


# ============================================================
# 辅助工具
# ============================================================

def _get_last_month(period: str) -> str:
    """获取上个月期间"""
    year, month = period.split("-")
    month = int(month) - 1
    if month == 0:
        month = 12
        year = str(int(year) - 1)
    return f"{year}-{month:02d}"


def _get_last_n_months(n: int) -> list:
    """获取近n个月"""
    today = date.today()
    months = []
    for i in range(n - 1, -1, -1):
        m = today - timedelta(days=i * 30)
        months.append(m.strftime("%Y-%m"))
    return months


def _calc_mom(current: float, previous: float) -> float:
    """计算环比百分比"""
    if previous == 0:
        return 0 if current == 0 else 100.0
    return ((current - previous) / abs(previous)) * 100


def _get_aging_level(days: int) -> str:
    """账龄等级"""
    if days <= 30:
        return "normal"
    elif days <= 90:
        return "attention"
    elif days <= 180:
        return "warning"
    else:
        return "danger"
