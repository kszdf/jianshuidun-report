"""
挂靠税费精算服务 - v0.2.0 新增
核心功能：挂靠税费计算器、先扣后返模式计算
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any


def _d(x):
    return Decimal(str(x)) if x is not None else Decimal('0')


def _round2(val: Decimal) -> float:
    """保留2位小数"""
    return float(val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


# ============================================================
# 挂靠税费精算计算器
# ============================================================

def calculate_affiliated_tax(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    挂靠税费精算计算器
    
    输入参数:
        contract_amount: 合同金额（含税价，价税合计）
        tax_rate: 适用税率（默认9%）
        management_fee_ratio: 挂靠费比例（如2%）
        vat_burden_rate: 增值税税负率（如2.5%）
        income_tax_burden_rate: 所得税税负率（如1.5%）
    
    输出: 各项税费明细
    """
    # 输入变量
    contract_amount = _d(params.get('contract_amount', 0))  # 价税合计
    tax_rate = _d(params.get('tax_rate', 9)) / Decimal('100')  # 税率
    mgmt_fee_ratio = _d(params.get('management_fee_ratio', 2)) / Decimal('100')  # 挂靠费比例
    vat_burden = _d(params.get('vat_burden_rate', 2.5)) / Decimal('100')  # 增值税税负率
    income_tax_burden = _d(params.get('income_tax_burden_rate', 1.5)) / Decimal('100')  # 所得税税负率

    # 1. 不含税金额 = 价税合计 / (1+税率)
    amount_no_tax = contract_amount / (Decimal('1') + tax_rate)

    # 2. 销项税额 = 不含税金额 × 税率
    output_tax = amount_no_tax * tax_rate

    # 3. 应交增值税 = 不含税金额 × 增值税税负率
    vat_payable = amount_no_tax * vat_burden

    # 4. 应交附加税 = 应交增值税 × 12%（城建7%+教育3%+地方教育2%）
    surtax_rate = Decimal('0.12')
    surtax_payable = vat_payable * surtax_rate

    # 5. 应交所得税 = 不含税金额 × 所得税税负率
    income_tax_payable = amount_no_tax * income_tax_burden

    # 6. 挂靠管理费 = 价税合计 × 挂靠费比例
    management_fee = contract_amount * mgmt_fee_ratio

    # 7. 印花税 = 不含税金额 × 0.03% × 2（购销双方）
    stamp_tax_rate = Decimal('0.0003') * Decimal('2')
    stamp_tax = amount_no_tax * stamp_tax_rate

    # 8. 合计扣款 = 增值税+附加税+所得税+印花税+管理费
    total_deduction = vat_payable + surtax_payable + income_tax_payable + stamp_tax + management_fee

    # 9. 需要进项税 = 销项税 - 应交增值税
    input_tax_needed = output_tax - vat_payable

    # 10. 账面利润总额 = 应交所得税 / 25%（倒推）
    income_tax_rate = Decimal('0.25')
    book_profit = income_tax_payable / income_tax_rate

    # 11. 需成本费用发票（不含税） = 不含税收入 - 印花税 - 附加税 - 利润
    cost_invoice_needed = amount_no_tax - stamp_tax - surtax_payable - book_profit

    # 12. 分红个税 = (利润 - 所得税) × 20%
    dividend_tax_rate = Decimal('0.2')
    dividend_tax = (book_profit - income_tax_payable) * dividend_tax_rate

    # 实际到手金额
    net_received = contract_amount - total_deduction

    # 综合成本发票（含税）= 需成本费用发票（不含税） + 需要的进项税
    cost_invoice_with_tax = cost_invoice_needed + input_tax_needed

    return {
        # 输入参数
        "input": {
            "contract_amount": _round2(contract_amount),
            "tax_rate": float(tax_rate * 100),
            "management_fee_ratio": float(mgmt_fee_ratio * 100),
            "vat_burden_rate": float(vat_burden * 100),
            "income_tax_burden_rate": float(income_tax_burden * 100),
        },
        # 基础计算
        "basic": {
            "amount_no_tax": _round2(amount_no_tax),  # 不含税金额
            "output_tax": _round2(output_tax),  # 销项税额
        },
        # 各项税费
        "tax_items": [
            {"name": "增值税", "amount": _round2(vat_payable), "category": "流转税"},
            {"name": "附加税（城建+教附", "amount": _round2(surtax_payable), "category": "附加税"},
            {"name": "企业所得税", "amount": _round2(income_tax_payable), "category": "所得税"},
            {"name": "印花税", "amount": _round2(stamp_tax), "category": "其他税"},
            {"name": "挂靠管理费", "amount": _round2(management_fee), "category": "管理费"},
        ],
        # 汇总
        "summary": {
            "total_tax": _round2(vat_payable + surtax_payable + income_tax_payable + stamp_tax),  # 税费合计
            "total_deduction": _round2(total_deduction),  # 合计扣款
            "net_received": _round2(net_received),  # 实际到手
            "comprehensive_tax_rate": _round2((total_deduction / contract_amount * 100) if contract_amount > 0 else Decimal('0')),  # 综合费率%
        },
        # 发票需求
        "invoice_need": {
            "input_tax_needed": _round2(input_tax_needed),  # 需要进项税
            "cost_invoice_needed_no_tax": _round2(cost_invoice_needed),  # 需成本费用发票（不含税）
            "cost_invoice_needed_with_tax": _round2(cost_invoice_with_tax),  # 需成本费用发票（含税）
            "book_profit": _round2(book_profit),  # 账面利润
            "dividend_tax": _round2(dividend_tax),  # 分红个税
        },
    }


# ============================================================
# 先扣后返模式计算
# ============================================================

def calculate_pre_deduct_return(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    先扣后返模式计算
    
    逻辑：
    1. 先按"无票情况"全额扣除（增值税=销项全额，所得税=收入×25%利润率）
    2. 再根据提供的进项发票和成本发票计算应返还金额
    3. 实付 = 合同金额 - 先扣总额 + 总返还
    
    输入参数:
        基础参数（与挂靠税费相同）
        provided_input_tax: 已提供进项税额
        provided_cost_invoice: 已提供成本发票金额（不含税）
    
    输出: 应扣总额、已抵扣、实付金额
    """
    # 基础参数
    contract_amount = _d(params.get('contract_amount', 0))
    tax_rate = _d(params.get('tax_rate', 9)) / Decimal('100')
    mgmt_fee_ratio = _d(params.get('management_fee_ratio', 2)) / Decimal('100')

    # 不含税金额和销项税
    amount_no_tax = contract_amount / (Decimal('1') + tax_rate)
    output_tax = amount_no_tax * tax_rate

    # 已提供的进项税
    provided_input_tax = _d(params.get('provided_input_tax', 0))
    # 已提供的成本发票（不含税）
    provided_cost_invoice = _d(params.get('provided_cost_invoice', 0))

    # ========== 第一步：先扣（按无票最大情况预扣） ==========
    # 增值税：先按销项全额扣（假设无进项）
    vat_pre_deduct = output_tax
    # 附加税：按全额增值税计算
    surtax_rate = Decimal('0.12')
    surtax_pre_deduct = vat_pre_deduct * surtax_rate
    # 所得税：先按25%利润率预扣（假设无成本票）
    income_tax_rate = Decimal('0.25')
    # 按收入的25%作为利润预扣（行业通常做法，或者按更高比例）
    # 这里简化：按收入的25%利润率预扣所得税
    income_tax_pre_deduct = amount_no_tax * Decimal('0.25') * income_tax_rate
    # 印花税
    stamp_tax_rate = Decimal('0.0003') * Decimal('2')
    stamp_tax = amount_no_tax * stamp_tax_rate
    # 管理费
    management_fee = contract_amount * mgmt_fee_ratio

    # 先扣总额
    total_pre_deduct = vat_pre_deduct + surtax_pre_deduct + income_tax_pre_deduct + stamp_tax + management_fee

    # ========== 第二步：后返（根据提供的发票返还） ==========
    # 1. 进项税返还：提供多少进项票，返还多少增值税（最多返还预扣的增值税）
    input_tax_return = min(provided_input_tax, vat_pre_deduct)
    
    # 附加税也相应减少（因为增值税少了，附加税也少）
    surtax_return = input_tax_return * surtax_rate

    # 2. 成本票返还：成本票抵扣利润，减少所得税
    # 返还 = min(提供成本票 × 25%, 预扣的所得税)
    income_tax_return = min(provided_cost_invoice * income_tax_rate, income_tax_pre_deduct)

    # 总返还金额
    total_return = input_tax_return + surtax_return + income_tax_return

    # ========== 第三步：实付 ==========
    actual_payment = contract_amount - total_pre_deduct + total_return

    # 目标税负（按税负率计算的正常应交）
    vat_burden = _d(params.get('vat_burden_rate', 2.5)) / Decimal('100')
    income_tax_burden = _d(params.get('income_tax_burden_rate', 1.5)) / Decimal('100')
    target_vat = amount_no_tax * vat_burden
    target_income_tax = amount_no_tax * income_tax_burden

    # 计算正常模式下的结果（用于对比）
    normal_result = calculate_affiliated_tax(params)

    return {
        **normal_result,  # 包含基础计算结果
        "pre_deduct_return": {
            # 先扣部分
            "pre_deduct": {
                "vat": _round2(vat_pre_deduct),  # 预扣增值税（全额）
                "surtax": _round2(surtax_pre_deduct),  # 预扣附加税
                "income_tax": _round2(income_tax_pre_deduct),  # 预扣所得税（按25%利润率）
                "stamp_tax": _round2(stamp_tax),  # 印花税
                "management_fee": _round2(management_fee),  # 管理费
                "total": _round2(total_pre_deduct),  # 先扣总额
            },
            # 返还部分
            "returns": {
                "input_tax_return": _round2(input_tax_return),  # 进项税返还
                "surtax_return": _round2(surtax_return),  # 附加税返还
                "income_tax_return": _round2(income_tax_return),  # 所得税返还
                "total_return": _round2(total_return),  # 总返还
            },
            # 提供的发票
            "provided": {
                "input_tax": _round2(provided_input_tax),  # 已提供进项税
                "cost_invoice_no_tax": _round2(provided_cost_invoice),  # 已提供成本票（不含税）
            },
            # 结果
            "result": {
                "actual_payment": _round2(actual_payment),  # 实付金额
                "actual_vat": _round2(vat_pre_deduct - input_tax_return),  # 实际增值税
                "actual_income_tax": _round2(income_tax_pre_deduct - income_tax_return),  # 实际所得税
            },
            # 缺口/超额
            "gap": {
                "input_tax_shortfall": _round2(max(output_tax - provided_input_tax, Decimal('0'))),  # 进项税缺口（相对销项）
                "input_tax_excess": _round2(max(provided_input_tax - output_tax, Decimal('0'))),  # 进项税超额
                "cost_invoice_shortfall": _round2(max(amount_no_tax * Decimal('0.75') - provided_cost_invoice, Decimal('0'))),  # 成本票缺口（按75%成本率）
            },
            # 目标税负对比
            "target_burden": {
                "target_vat": _round2(target_vat),  # 目标增值税（按税负率）
                "target_income_tax": _round2(target_income_tax),  # 目标所得税（按税负率）
                "is_vat_below_target": (vat_pre_deduct - input_tax_return) < target_vat,  # 实际增值税是否低于目标
                "is_income_tax_below_target": (income_tax_pre_deduct - income_tax_return) < target_income_tax,  # 实际所得税是否低于目标
            },
            "conclusion": f"先扣{_round2(total_pre_deduct)}元，返还{_round2(total_return)}元，实付{_round2(actual_payment)}元",
        }
    }


# ============================================================
# 税率变动比价器
# ============================================================

def calculate_tax_rate_comparison(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    税率变动比价器
    
    输入参数:
        amount: 金额（含税或不含税，根据amount_type判断）
        amount_type: 金额类型 "with_tax" 或 "no_tax"
        old_rate: 旧税率%
        new_rate: 新税率%
    
    输出: 不含税金额变化、税额变化、价税合计变化
    """
    amount = _d(params.get('amount', 0))
    amount_type = params.get('amount_type', 'with_tax')
    old_rate = _d(params.get('old_rate', 13)) / Decimal('100')
    new_rate = _d(params.get('new_rate', 9)) / Decimal('100')

    # 先算旧税率下的各项
    if amount_type == 'with_tax':
        # 输入的是含税价
        old_price_with_tax = amount
        old_amount_no_tax = amount / (Decimal('1') + old_rate)
        old_tax = old_amount_no_tax * old_rate
    else:
        # 输入的是不含税价
        old_amount_no_tax = amount
        old_tax = amount * old_rate
        old_price_with_tax = amount + old_tax

    # 新税率下的各项（保持不含税金额不变）
    new_amount_no_tax = old_amount_no_tax
    new_tax = new_amount_no_tax * new_rate
    new_price_with_tax = new_amount_no_tax + new_tax

    # 变化
    tax_diff = new_tax - old_tax
    price_diff = new_price_with_tax - old_price_with_tax
    amount_no_tax_diff = new_amount_no_tax - old_amount_no_tax

    # 对利润的影响（不含税成本不变时，税额变化就是利润变化
    profit_impact = -tax_diff  # 税减少则利润增加

    return {
        "old": {
            "rate": float(old_rate * 100),
            "amount_no_tax": _round2(old_amount_no_tax),
            "tax": _round2(old_tax),
            "price_with_tax": _round2(old_price_with_tax),
        },
        "new": {
            "rate": float(new_rate * 100),
            "amount_no_tax": _round2(new_amount_no_tax),
            "tax": _round2(new_tax),
            "price_with_tax": _round2(new_price_with_tax),
        },
        "diff": {
            "amount_no_tax_diff": _round2(amount_no_tax_diff),
            "tax_diff": _round2(tax_diff),
            "price_with_tax_diff": _round2(price_diff),
            "profit_impact": _round2(profit_impact),
            "tax_change_rate": _round2((tax_diff / old_tax * 100) if old_tax > 0 else Decimal('0')),
        },
        "conclusion": f"税率从{float(old_rate*100):.0f}%降到{float(new_rate*100):.0f}%，"
                      f"税额减少{_round2(-tax_diff)}元，"
                      f"价税合计减少{_round2(-price_diff)}元，"
                      f"对利润的影响：+{_round2(profit_impact)}元",
    }


# ============================================================
# 混合销售平衡点测算
# ============================================================

def calculate_mixed_sales_break_even(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    混合销售平衡点测算
    货物销售+安装服务的平衡点计算
    
    输入参数:
        goods_amount: 货物金额（含税）
        install_amount: 安装金额（含税）
        goods_rate: 货物税率%（默认13%）
        install_rate: 安装税率%（默认9%）
        mixed_rate: 混合销售税率%（默认13%，从高适用）
    
    输出: 分开签合同 vs 合并签合同的税负差异
    """
    goods_amount = _d(params.get('goods_amount', 0))
    install_amount = _d(params.get('install_amount', 0))
    goods_rate = _d(params.get('goods_rate', 13)) / Decimal('100')
    install_rate = _d(params.get('install_rate', 9)) / Decimal('100')
    mixed_rate = _d(params.get('mixed_rate', 13)) / Decimal('100')  # 从高适用

    # 分开签合同
    goods_no_tax = goods_amount / (Decimal('1') + goods_rate)
    goods_tax = goods_no_tax * goods_rate
    install_no_tax = install_amount / (Decimal('1') + install_rate)
    install_tax = install_no_tax * install_rate

    separate_total_no_tax = goods_no_tax + install_no_tax
    separate_total_tax = goods_tax + install_tax
    separate_total_price = goods_amount + install_amount

    # 合并签合同（混合销售，从高适用税率）
    mixed_total_price = goods_amount + install_amount
    mixed_total_no_tax = mixed_total_price / (Decimal('1') + mixed_rate)
    mixed_total_tax = mixed_total_no_tax * mixed_rate

    # 差异
    tax_diff = mixed_total_tax - separate_total_tax
    no_tax_diff = mixed_total_no_tax - separate_total_no_tax

    # 平衡点：当货物占比多少时，两种方式税负相等
    # 设货物占比为x，总金额为S
    # 分开: S*x/(1+gr)*gr + S*(1-x)/(1+ir)*ir
    # 合并: S/(1+mr)*mr
    # 平衡点方程: x*gr/(1+gr) + (1-x)*ir/(1+ir) = mr/(1+mr)
    # x = (mr/(1+mr) - ir/(1+ir)) / (gr/(1+gr) - ir/(1+ir))
    
    gr_term = goods_rate / (Decimal('1') + goods_rate)
    ir_term = install_rate / (Decimal('1') + install_rate)
    mr_term = mixed_rate / (Decimal('1') + mixed_rate)

    if gr_term != ir_term:
        break_even_ratio = (mr_term - ir_term) / (gr_term - ir_term) * 100
    else:
        break_even_ratio = Decimal('0')

    # 当前货物占比
    total_price = goods_amount + install_amount
    current_goods_ratio = (goods_amount / total_price * 100) if total_price > 0 else Decimal('0')

    # 建议
    if tax_diff > 0:
        suggestion = "建议分开签合同，可节税"
    elif tax_diff < 0:
        suggestion = "建议合并签合同，可节税"
    else:
        suggestion = "两种方式税负相同"

    return {
        "separate": {
            "goods_no_tax": _round2(goods_no_tax),
            "goods_tax": _round2(goods_tax),
            "install_no_tax": _round2(install_no_tax),
            "install_tax": _round2(install_tax),
            "total_no_tax": _round2(separate_total_no_tax),
            "total_tax": _round2(separate_total_tax),
            "total_price": _round2(separate_total_price),
        },
        "mixed": {
            "total_no_tax": _round2(mixed_total_no_tax),
            "total_tax": _round2(mixed_total_tax),
            "total_price": _round2(mixed_total_price),
            "applied_rate": float(mixed_rate * 100),
        },
        "comparison": {
            "tax_diff": _round2(tax_diff),
            "no_tax_diff": _round2(no_tax_diff),
            "saving_amount": _round2(abs(tax_diff)),
            "better_option": "分开签合同" if tax_diff > 0 else ("合并签合同" if tax_diff < 0 else "无差异"),
        },
        "break_even": {
            "break_even_ratio": _round2(break_even_ratio),  # 平衡点货物占比%
            "current_goods_ratio": _round2(current_goods_ratio),  # 当前货物占比%
            "explanation": f"当货物金额占比为{_round2(break_even_ratio)}%时，两种方式税负相等",
        },
        "suggestion": suggestion,
    }
