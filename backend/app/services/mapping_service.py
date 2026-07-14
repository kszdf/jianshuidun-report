"""
科目映射服务 - 自动匹配企业科目到标准科目
核心：零重复录入，财务只导出Excel，系统自动识别映射
"""
import re
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
from decimal import Decimal

from app.models.config import CfgStdSubject, CfgSubjectMapping


# 关键词匹配规则 - 建筑行业特色科目
# 格式: (报表分类, 关键词列表, 匹配优先级)
KEYWORD_RULES = [
    # 资产类 - 资金
    ("asset_cash", ["库存现金", "现金"], 100),
    ("asset_cash", ["银行存款"], 95),
    ("asset_cash", ["其他货币资金"], 90),
    # 资产类 - 应收
    ("asset_ar", ["应收账款", "应收工程款", "应收劳务费"], 95),
    ("asset_ar", ["应收票据"], 80),
    ("asset_pre_receive", ["预付账款", "预付工程款", "预付材料款"], 85),
    # 资产类 - 存货/工程施工
    ("asset_inventory", ["原材料", "库存材料", "周转材料"], 90),
    ("asset_inventory", ["工程施工", "合同履约成本", "施工成本"], 95),
    ("asset_inventory", ["机械作业"], 80),
    # 资产类 - 其他
    ("asset_fixed", ["固定资产", "累计折旧"], 90),
    ("asset_intangible", ["无形资产", "累计摊销"], 90),
    # 负债类
    ("liability_ap", ["应付账款", "应付工程款", "应付材料款"], 95),
    ("liability_ap", ["应付票据"], 80),
    ("liability_pre_receive", ["预收账款", "预收工程款"], 90),
    ("liability_salary", ["应付职工薪酬", "应付工资"], 90),
    ("liability_tax", ["应交税费", "应交税金"], 90),
    # 权益类
    ("equity_capital", ["实收资本", "股本"], 90),
    ("equity_surplus", ["盈余公积"], 90),
    ("equity_profit", ["本年利润", "利润分配"], 90),
    # 收入类 - 建筑行业核心
    ("income_main", ["主营业务收入", "工程结算收入", "工程结算", "建造合同收入"], 100),
    ("income_main", ["工程结算收入"], 95),
    ("income_other", ["其他业务收入"], 85),
    # 成本类 - 建筑行业核心
    ("cost", ["主营业务成本", "工程结算成本", "合同履约成本"], 100),
    ("cost_labor", ["人工费", "劳务成本", "工资"], 90),
    ("cost_material", ["材料费", "原材料", "主材", "辅材"], 90),
    ("cost_machine", ["机械费", "机械使用费", "机械台班"], 90),
    ("cost_other", ["其他直接费", "措施费", "安全文明施工费"], 80),
    # 费用类
    ("expense_manage", ["管理费用"], 95),
    ("expense_sale", ["销售费用", "营业费用"], 90),
    ("expense_finance", ["财务费用", "利息", "手续费"], 85),
    ("expense_tax", ["税金及附加", "营业税金及附加"], 90),
]


def auto_map_subjects(db: Session, company_id: int, subjects: List[Dict]) -> Dict:
    """
    自动科目映射
    输入: 企业科目列表 [{code, name, full_name, ...}]
    输出: {total, mapped_count, items: [{source_code, source_name, std_subject_id, std_subject_code, std_subject_name, confidence, is_mapped, match_type}]}
    """
    # 1. 获取所有标准科目
    std_subjects = db.query(CfgStdSubject).filter(
        (CfgStdSubject.company_id == 0) | (CfgStdSubject.company_id == company_id)
    ).all()
    std_by_code = {s.subject_code: s for s in std_subjects}
    std_by_category = {}
    for s in std_subjects:
        if s.report_category not in std_by_category:
            std_by_category[s.report_category] = []
        std_by_category[s.report_category].append(s)

    # 2. 获取已有映射（增量更新）
    existing_mappings = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id
    ).all()
    existing_by_code = {m.source_code: m for m in existing_mappings}

    # 3. 逐个匹配
    results = []
    mapped_count = 0

    for subj in subjects:
        code = subj.get("code", "")
        name = subj.get("name", "")
        full_name = subj.get("full_name", name)

        # 已有映射且是手动映射的，保留
        if code in existing_by_code:
            old = existing_by_code[code]
            if old.match_type == "manual" and old.is_mapped:
                results.append({
                    "source_code": code,
                    "source_name": name,
                    "source_full_name": full_name,
                    "std_subject_id": old.std_subject_id,
                    "std_subject_code": old.std_subject_code,
                    "std_subject_name": old.std_subject_name,
                    "match_confidence": float(old.match_confidence),
                    "is_mapped": True,
                    "match_type": "manual",
                })
                mapped_count += 1
                continue

        # 自动匹配
        std_id, std_code, std_name, confidence = _match_one_subject(
            code, name, full_name, std_by_code, std_by_category
        )

        is_mapped = confidence >= 60
        if is_mapped:
            mapped_count += 1

        results.append({
            "source_code": code,
            "source_name": name,
            "source_full_name": full_name,
            "std_subject_id": std_id,
            "std_subject_code": std_code,
            "std_subject_name": std_name,
            "match_confidence": round(confidence, 2),
            "is_mapped": is_mapped,
            "match_type": "auto",
        })

    # 4. 写入/更新映射表
    for r in results:
        if r["source_code"] in existing_by_code:
            m = existing_by_code[r["source_code"]]
            m.source_name = r["source_name"]
            m.source_full_name = r["source_full_name"]
            m.std_subject_id = r["std_subject_id"]
            m.std_subject_code = r["std_subject_code"]
            m.std_subject_name = r["std_subject_name"]
            m.match_confidence = Decimal(str(r["match_confidence"]))
            m.is_mapped = r["is_mapped"]
            if m.match_type != "manual":
                m.match_type = r["match_type"]
        else:
            m = CfgSubjectMapping(
                company_id=company_id,
                source_code=r["source_code"],
                source_name=r["source_name"],
                source_full_name=r["source_full_name"],
                std_subject_id=r["std_subject_id"],
                std_subject_code=r["std_subject_code"],
                std_subject_name=r["std_subject_name"],
                match_type=r["match_type"],
                match_confidence=Decimal(str(r["match_confidence"])),
                is_mapped=r["is_mapped"],
            )
            db.add(m)

    db.commit()

    return {
        "total": len(results),
        "mapped_count": mapped_count,
        "auto_mapped": sum(1 for r in results if r["match_type"] == "auto" and r["is_mapped"]),
        "manual_locked": sum(1 for r in results if r["match_type"] == "manual"),
        "need_review": sum(1 for r in results if not r["is_mapped"] or r["match_confidence"] < 80),
        "items": results,
    }


def _match_one_subject(code: str, name: str, full_name: str,
                        std_by_code: Dict, std_by_category: Dict) -> Tuple[int, str, str, float]:
    """
    匹配单个科目
    返回: (std_id, std_code, std_name, confidence)
    """
    best_category = None
    best_confidence = 0

    name_lower = name.lower()
    full_lower = full_name.lower()

    # 策略1: 关键词规则匹配（建筑行业特色）
    for category, keywords, base_score in KEYWORD_RULES:
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in name_lower:
                score = base_score
                # 完全匹配加分
                if kw_lower == name_lower:
                    score += 5
                if score > best_confidence:
                    best_confidence = score
                    best_category = category
                break  # 匹配到一个关键词就行

    # 策略2: 科目编码前缀匹配
    if code:
        # 常见编码规则：1开头资产，2负债，3权益，4成本，5/6损益
        if code.startswith("1") and not best_category:
            best_category = "asset_other"
            best_confidence = 40
        elif code.startswith("2") and not best_category:
            best_category = "liability_other"
            best_confidence = 40
        elif code.startswith("4") and not best_category:
            best_category = "cost"
            best_confidence = 50
        elif code.startswith("5") and "收入" in name:
            if best_confidence < 60:
                best_category = "income_other"
                best_confidence = 55
        elif code.startswith("5") and "成本" in name:
            if best_confidence < 60:
                best_category = "cost"
                best_confidence = 55
        elif code.startswith("6") and "费用" in name:
            if best_confidence < 60:
                best_category = "expense_manage"
                best_confidence = 55

    # 策略3: 名称相似度（简易版 - 包含关系）
    if best_category and best_category in std_by_category:
        std_list = std_by_category[best_category]
        if std_list:
            # 取分类下的第一个科目作为映射目标
            # 实际报表计算时是按report_category分组的，具体映射到哪个标准科目不重要
            std = std_list[0]
            return std.id, std.subject_code, std.subject_name, best_confidence

    # 兜底：未匹配
    return None, None, None, 0


def get_unmapped_subjects(db: Session, company_id: int) -> List:
    """获取未映射的科目列表"""
    unmapped = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.is_mapped == False,
    ).order_by(CfgSubjectMapping.source_code).all()
    return unmapped


def get_mapping_stats(db: Session, company_id: int) -> Dict:
    """获取映射统计"""
    total = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id
    ).count()
    mapped = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.is_mapped == True,
    ).count()
    auto = db.query(CfgSubjectMapping).filter(
        CfgSubjectMapping.company_id == company_id,
        CfgSubjectMapping.match_type == "auto",
        CfgSubjectMapping.is_mapped == True,
    ).count()
    manual = mapped - auto

    return {
        "total": total,
        "mapped": mapped,
        "unmapped": total - mapped,
        "auto_mapped": auto,
        "manual_mapped": manual,
        "mapping_rate": round(mapped / total * 100, 1) if total > 0 else 0,
    }
