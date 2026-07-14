"""
现金流预测服务 - v0.2.0 新增
核心功能：3个月滚动预测，支持查看6个月数据
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from app.models.business_ext import BizCashflowForecast, BizCashflowForecastItem
from app.models.business import BizBankAccount


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
# 现金流预测列表
# ============================================================

def get_forecast_list(db: Session, company_id: int) -> dict:
    """获取现金流预测列表"""
    forecasts = db.query(BizCashflowForecast).filter(
        BizCashflowForecast.company_id == company_id,
    ).order_by(BizCashflowForecast.id.desc()).all()

    return {
        "total": len(forecasts),
        "items": [
            {
                "id": f.id,
                "name": f.forecast_name,
                "start_month": f.start_month,
                "months_count": f.months_count,
                "opening_balance": _round2(f.opening_balance),
                "safety_line": _round2(f.safety_line),
                "status": f.status,
                "created_at": str(f.created_at) if f.created_at else "",
            }
            for f in forecasts
        ]
    }


# ============================================================
# 现金流预测详情
# ============================================================

def get_forecast_detail(db: Session, company_id: int, forecast_id: int) -> dict:
    """获取现金流预测详情"""
    forecast = db.query(BizCashflowForecast).filter(
        BizCashflowForecast.company_id == company_id,
        BizCashflowForecast.id == forecast_id,
    ).first()

    if not forecast:
        return {"error": "预测不存在"}

    # 获取明细项
    items = db.query(BizCashflowForecastItem).filter(
        BizCashflowForecastItem.forecast_id == forecast_id,
    ).order_by(BizCashflowForecastItem.sort_order, BizCashflowForecastItem.id).all()

    # 按类型和月份分组
    income_items = []
    expense_items = []
    for item in items:
        item_dict = {
            "id": item.id,
            "item_type": item.item_type,
            "category": item.category,
            "item_name": item.item_name,
            "amount": _round2(item.amount),
            "month": item.month,
            "related_project": item.related_project,
            "remark": item.remark,
        }
        if item.item_type == 'income':
            income_items.append(item_dict)
        else:
            expense_items.append(item_dict)

    # 计算月度汇总
    monthly_data = _calculate_monthly_forecast(
        _to_float(forecast.opening_balance),
        _to_float(forecast.frozen_balance),
        forecast.start_month,
        forecast.months_count,
        income_items,
        expense_items,
        _to_float(forecast.safety_line),
    )

    return {
        "forecast": {
            "id": forecast.id,
            "name": forecast.forecast_name,
            "start_month": forecast.start_month,
            "months_count": forecast.months_count,
            "opening_balance": _round2(forecast.opening_balance),
            "frozen_balance": _round2(forecast.frozen_balance),
            "safety_line": _round2(forecast.safety_line),
            "status": forecast.status,
        },
        "income_items": income_items,
        "expense_items": expense_items,
        "monthly_data": monthly_data,
    }


def _calculate_monthly_forecast(opening_balance: float, frozen_balance: float,
                                 start_month: str, months_count: int,
                                 income_items: list, expense_items: list,
                                 safety_line: float) -> list:
    """计算月度现金流预测"""
    result = []
    current_balance = opening_balance  # 可动用资金期初余额

    # 生成月份列表
    year, month = map(int, start_month.split('-'))
    months = []
    for i in range(months_count):
        m = date(year, month, 1) + relativedelta(months=i)
        months.append(m.strftime("%Y-%m"))

    for m in months:
        # 本月收入合计
        month_income = sum(item["amount"] for item in income_items if item["month"] == m)
        # 本月支出合计
        month_expense = sum(item["amount"] for item in expense_items if item["month"] == m)
        # 净现金流
        net_flow = month_income - month_expense
        # 期末余额
        ending_balance = current_balance + net_flow

        # 资金预警
        is_warning = ending_balance < safety_line
        warning_level = "danger" if ending_balance < safety_line * 0.5 else ("warning" if is_warning else "normal")

        result.append({
            "month": m,
            "opening_balance": _round2(current_balance),
            "total_income": _round2(month_income),
            "total_expense": _round2(month_expense),
            "net_flow": _round2(net_flow),
            "ending_balance": _round2(ending_balance),
            "frozen_balance": _round2(frozen_balance),
            "available_balance": _round2(ending_balance),  # 可动用余额
            "is_warning": is_warning,
            "warning_level": warning_level,
        })

        # 下月期初 = 本月期末
        current_balance = ending_balance

    return result


# ============================================================
# 创建/更新预测
# ============================================================

def create_forecast(db: Session, company_id: int, data: dict) -> dict:
    """创建现金流预测"""
    forecast = BizCashflowForecast(
        company_id=company_id,
        forecast_name=data.get("name", "现金流预测"),
        start_month=data.get("start_month", date.today().strftime("%Y-%m")),
        months_count=data.get("months_count", 3),
        opening_balance=Decimal(str(data.get("opening_balance", 0))),
        frozen_balance=Decimal(str(data.get("frozen_balance", 0))),
        safety_line=Decimal(str(data.get("safety_line", 0))),
        status="draft",
    )
    db.add(forecast)
    db.flush()

    # 添加明细项
    for item in data.get("income_items", []):
        db.add(BizCashflowForecastItem(
            forecast_id=forecast.id,
            item_type="income",
            category=item.get("category", "其他"),
            item_name=item.get("item_name", ""),
            amount=Decimal(str(item.get("amount", 0))),
            month=item.get("month", forecast.start_month),
            related_project=item.get("related_project"),
            remark=item.get("remark"),
            sort_order=item.get("sort_order", 0),
        ))

    for item in data.get("expense_items", []):
        db.add(BizCashflowForecastItem(
            forecast_id=forecast.id,
            item_type="expense",
            category=item.get("category", "其他"),
            item_name=item.get("item_name", ""),
            amount=Decimal(str(item.get("amount", 0))),
            month=item.get("month", forecast.start_month),
            related_project=item.get("related_project"),
            remark=item.get("remark"),
            sort_order=item.get("sort_order", 0),
        ))

    db.commit()

    return {"id": forecast.id, "message": "创建成功"}


# ============================================================
# 获取银行账户期初余额
# ============================================================

def get_bank_accounts_for_forecast(db: Session, company_id: int) -> list:
    """获取银行账户列表（用于设置期初资金）"""
    accounts = db.query(BizBankAccount).filter(
        BizBankAccount.company_id == company_id,
    ).order_by(BizBankAccount.sort_order, BizBankAccount.id).all()

    result = []
    total_available = 0
    total_frozen = 0

    for acc in accounts:
        balance = _to_float(acc.current_balance)
        # 保证金户等视为不可动用
        is_frozen = "保证金" in (acc.account_name or "") or acc.account_type == "frozen"
        if is_frozen:
            total_frozen += balance
        else:
            total_available += balance

        result.append({
            "id": acc.id,
            "account_name": acc.account_name,
            "bank_name": acc.bank_name,
            "account_no": acc.account_no,
            "balance": _round2(balance),
            "is_frozen": is_frozen,
        })

    return {
        "accounts": result,
        "total_available": _round2(total_available),
        "total_frozen": _round2(total_frozen),
        "total_balance": _round2(total_available + total_frozen),
    }


# ============================================================
# 收入/支出类别选项
# ============================================================

INCOME_CATEGORIES = [
    {"value": "工程款", "label": "工程款"},
    {"value": "材料款", "label": "材料款（销售）"},
    {"value": "劳务收入", "label": "劳务收入"},
    {"value": "其他收入", "label": "其他收入"},
]

EXPENSE_CATEGORIES = [
    {"value": "人工费", "label": "人工费"},
    {"value": "材料费", "label": "材料费"},
    {"value": "机械费", "label": "机械费"},
    {"value": "分包款", "label": "分包款"},
    {"value": "税费", "label": "税费"},
    {"value": "管理费", "label": "管理费"},
    {"value": "其他支出", "label": "其他支出"},
]


def get_forecast_categories() -> dict:
    """获取预测收支类别选项"""
    return {
        "income_categories": INCOME_CATEGORIES,
        "expense_categories": EXPENSE_CATEGORIES,
    }
