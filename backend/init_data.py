"""
初始化数据脚本 - 建筑行业标准科目 + 演示数据
运行: python init_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal
from app.core.security import hash_password
from app.models.system import SysUser, SysCompany
from app.models.config import CfgStdSubject
from app.models.business import BizProject, BizCustomer, BizBankAccount
from app.models.finance import AccSubjectBalance, AccVoucher, AccVoucherItem
from datetime import date, datetime
from decimal import Decimal


# ============================================================
# 建筑行业标准科目表（精简版，覆盖报表所需分类）
# ============================================================

STD_SUBJECTS = [
    # 资产类
    {"code": "1001", "name": "库存现金", "type": "asset", "category": "asset_cash", "level": 1, "parent": ""},
    {"code": "1002", "name": "银行存款", "type": "asset", "category": "asset_cash", "level": 1, "parent": ""},
    {"code": "1012", "name": "其他货币资金", "type": "asset", "category": "asset_cash", "level": 1, "parent": ""},
    {"code": "1121", "name": "应收票据", "type": "asset", "category": "asset_ar", "level": 1, "parent": ""},
    {"code": "1122", "name": "应收账款", "type": "asset", "category": "asset_ar", "level": 1, "parent": ""},
    {"code": "112201", "name": "应收工程款", "type": "asset", "category": "asset_ar", "level": 2, "parent": "1122"},
    {"code": "112202", "name": "应收销货款", "type": "asset", "category": "asset_ar", "level": 2, "parent": "1122"},
    {"code": "1123", "name": "预付账款", "type": "asset", "category": "asset_pre_pay", "level": 1, "parent": ""},
    {"code": "112301", "name": "预付工程款", "type": "asset", "category": "asset_pre_pay", "level": 2, "parent": "1123"},
    {"code": "112302", "name": "预付材料款", "type": "asset", "category": "asset_pre_pay", "level": 2, "parent": "1123"},
    {"code": "1221", "name": "其他应收款", "type": "asset", "category": "asset_other", "level": 1, "parent": ""},
    {"code": "1403", "name": "原材料", "type": "asset", "category": "asset_inventory", "level": 1, "parent": ""},
    {"code": "1411", "name": "周转材料", "type": "asset", "category": "asset_inventory", "level": 1, "parent": ""},
    {"code": "1521", "name": "合同履约成本", "type": "asset", "category": "asset_inventory", "level": 1, "parent": ""},
    {"code": "1522", "name": "工程施工", "type": "asset", "category": "asset_inventory", "level": 1, "parent": ""},
    {"code": "1523", "name": "机械作业", "type": "asset", "category": "asset_inventory", "level": 1, "parent": ""},
    {"code": "1601", "name": "固定资产", "type": "asset", "category": "asset_fixed", "level": 1, "parent": ""},
    {"code": "1602", "name": "累计折旧", "type": "asset", "category": "asset_fixed", "level": 1, "parent": ""},
    {"code": "1701", "name": "无形资产", "type": "asset", "category": "asset_intangible", "level": 1, "parent": ""},

    # 负债类
    {"code": "2201", "name": "应付票据", "type": "asset", "category": "liability_ap", "level": 1, "parent": ""},
    {"code": "2202", "name": "应付账款", "type": "liability", "category": "liability_ap", "level": 1, "parent": ""},
    {"code": "220201", "name": "应付工程款", "type": "liability", "category": "liability_ap", "level": 2, "parent": "2202"},
    {"code": "220202", "name": "应付材料款", "type": "liability", "category": "liability_ap", "level": 2, "parent": "2202"},
    {"code": "2203", "name": "预收账款", "type": "liability", "category": "liability_pre_receive", "level": 1, "parent": ""},
    {"code": "220301", "name": "预收工程款", "type": "liability", "category": "liability_pre_receive", "level": 2, "parent": "2203"},
    {"code": "2211", "name": "应付职工薪酬", "type": "liability", "category": "liability_salary", "level": 1, "parent": ""},
    {"code": "2221", "name": "应交税费", "type": "liability", "category": "liability_tax", "level": 1, "parent": ""},

    # 权益类
    {"code": "4001", "name": "实收资本", "type": "equity", "category": "equity_capital", "level": 1, "parent": ""},
    {"code": "4101", "name": "盈余公积", "type": "equity", "category": "equity_surplus", "level": 1, "parent": ""},
    {"code": "4103", "name": "本年利润", "type": "equity", "category": "equity_profit", "level": 1, "parent": ""},
    {"code": "4104", "name": "利润分配", "type": "equity", "category": "equity_profit", "level": 1, "parent": ""},

    # 成本类
    {"code": "5401", "name": "工程施工", "type": "cost", "category": "cost", "level": 1, "parent": ""},
    {"code": "540101", "name": "合同成本", "type": "cost", "category": "cost", "level": 2, "parent": "5401"},
    {"code": "54010101", "name": "人工费", "type": "cost", "category": "cost_labor", "level": 3, "parent": "540101"},
    {"code": "54010102", "name": "材料费", "type": "cost", "category": "cost_material", "level": 3, "parent": "540101"},
    {"code": "54010103", "name": "机械使用费", "type": "cost", "category": "cost_machine", "level": 3, "parent": "540101"},
    {"code": "54010104", "name": "其他直接费", "type": "cost", "category": "cost_other", "level": 3, "parent": "540101"},
    {"code": "540102", "name": "间接费用", "type": "cost", "category": "cost_other", "level": 2, "parent": "5401"},
    {"code": "5402", "name": "工程结算", "type": "cost", "category": "cost_settlement", "level": 1, "parent": ""},
    {"code": "5403", "name": "机械作业", "type": "cost", "category": "cost_machine", "level": 1, "parent": ""},

    # 损益类 - 收入
    {"code": "6001", "name": "主营业务收入", "type": "income", "category": "income_main", "level": 1, "parent": ""},
    {"code": "600101", "name": "工程结算收入", "type": "income", "category": "income_main", "level": 2, "parent": "6001"},
    {"code": "600102", "name": "劳务收入", "type": "income", "category": "income_main", "level": 2, "parent": "6001"},
    {"code": "6051", "name": "其他业务收入", "type": "income", "category": "income_other", "level": 1, "parent": ""},

    # 损益类 - 成本费用
    {"code": "6401", "name": "主营业务成本", "type": "expense", "category": "cost", "level": 1, "parent": ""},
    {"code": "6403", "name": "税金及附加", "type": "expense", "category": "expense_tax", "level": 1, "parent": ""},
    {"code": "6601", "name": "销售费用", "type": "expense", "category": "expense_sale", "level": 1, "parent": ""},
    {"code": "6602", "name": "管理费用", "type": "expense", "category": "expense_manage", "level": 1, "parent": ""},
    {"code": "6603", "name": "财务费用", "type": "expense", "category": "expense_finance", "level": 1, "parent": ""},
]


def init_std_subjects(db: Session):
    """初始化标准科目"""
    existing = db.query(CfgStdSubject).filter(CfgStdSubject.company_id == 0).count()
    if existing > 0:
        print(f"标准科目已存在 ({existing} 条)，跳过")
        return

    for i, s in enumerate(STD_SUBJECTS):
        subj = CfgStdSubject(
            company_id=0,
            subject_code=s["code"],
            subject_name=s["name"],
            parent_code=s["parent"],
            subject_type=s["type"],
            report_category=s["category"],
            level=s["level"],
            sort_order=i + 1,
            is_leaf=s["level"] >= 3 or (s["level"] == 1 and not any(x["parent"] == s["code"] for x in STD_SUBJECTS)),
        )
        db.add(subj)

    db.commit()
    print(f"已初始化 {len(STD_SUBJECTS)} 条建筑行业标准科目")


def init_company_and_user(db: Session):
    """初始化演示公司和用户"""
    # 公司
    company = db.query(SysCompany).filter(SysCompany.id == 1).first()
    if not company:
        company = SysCompany(
            id=1,
            name="苏州建鑫建设工程有限公司",
            tax_no="91320500MA12345678",
            industry="建筑工程",
            contact="张总",
            phone="13812345678",
        )
        db.add(company)
        db.commit()
        print("已创建演示公司")

    # 用户 - boss
    boss = db.query(SysUser).filter(SysUser.username == "boss").first()
    if not boss:
        boss = SysUser(
            company_id=1,
            username="boss",
            password_hash=hash_password("123456"),
            real_name="张总",
            role="boss",
            email="boss@jianxin.com",
            phone="13812345678",
        )
        db.add(boss)

    # 用户 - 财务
    finance = db.query(SysUser).filter(SysUser.username == "finance").first()
    if not finance:
        finance = SysUser(
            company_id=1,
            username="finance",
            password_hash=hash_password("123456"),
            real_name="李会计",
            role="finance",
            email="finance@jianxin.com",
            phone="13987654321",
        )
        db.add(finance)

    db.commit()
    print("已创建演示用户: boss/123456, finance/123456")


def init_demo_projects(db: Session):
    """初始化演示项目 - v0.2.0 3个核心类型项目"""
    existing = db.query(BizProject).filter(BizProject.company_id == 1).count()
    if existing > 0:
        print(f"演示项目已存在 ({existing} 个)，跳过")
        return

    # 3个核心项目：房建/市政/装修，类型不同，人材机占比不同
    projects = [
        # 房建工程 - 人工30% 材料60% 机械10%
        {"name": "苏州工业园区科技园区办公楼项目", "customer": "苏州科技发展有限公司",
         "amount": 58000000, "budget": 49300000, "status": "ongoing",
         "start": "2026-03-15", "end": "2027-09-30", "manager": "王经理", "type": "房建工程"},
        # 市政工程 - 人工20% 材料55% 机械25%
        {"name": "吴中区市政道路改造项目", "customer": "吴中区市政公用局",
         "amount": 15600000, "budget": 13260000, "status": "ongoing",
         "start": "2026-04-20", "end": "2026-12-20", "manager": "陈工", "type": "市政工程"},
        # 装修工程 - 人工40% 材料55% 机械5%
        {"name": "高新区产业园精装修工程", "customer": "苏州高新产业园运营公司",
         "amount": 8600000, "budget": 7310000, "status": "ongoing",
         "start": "2026-05-10", "end": "2026-11-10", "manager": "刘工", "type": "装修工程"},
        # 房建工程 - 已完工
        {"name": "相城区人才公寓一期工程", "customer": "相城城建投资有限公司",
         "amount": 32000000, "budget": 27200000, "status": "completed",
         "start": "2025-01-10", "end": "2026-06-30", "manager": "赵经理", "type": "房建工程"},
    ]

    for i, p in enumerate(projects):
        proj = BizProject(
            company_id=1,
            project_code=f"XM{2026000 + i + 1}",
            project_name=p["name"],
            customer_name=p["customer"],
            contract_amount=Decimal(str(p["amount"])),
            budget_cost=Decimal(str(p["budget"])),
            start_date=datetime.strptime(p["start"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(p["end"], "%Y-%m-%d").date(),
            status=p["status"],
            manager=p["manager"],
            source="manual",
            remark=p["type"],  # 用remark存工程类型
        )
        db.add(proj)

    db.commit()
    print(f"已创建 {len(projects)} 个演示项目（房建/市政/装修三类）")


def init_demo_bank_accounts(db: Session):
    """初始化演示银行账户"""
    existing = db.query(BizBankAccount).filter(BizBankAccount.company_id == 1).count()
    if existing > 0:
        print(f"银行账户已存在 ({existing} 个)，跳过")
        return

    accounts = [
        {"name": "工行基本户", "bank": "工商银行苏州分行", "no": "1102023456789012345", "type": "basic", "bal": 8520000.00},
        {"name": "建行一般户", "bank": "建设银行姑苏支行", "no": "3220198765432109876", "type": "general", "bal": 3210000.00},
        {"name": "农行保证金户", "bank": "农业银行园区支行", "no": "1055012345678901234", "type": "general", "bal": 1500000.00},
    ]

    for i, a in enumerate(accounts):
        acc = BizBankAccount(
            company_id=1,
            account_name=a["name"],
            bank_name=a["bank"],
            account_no=a["no"],
            account_type=a["type"],
            is_outer=False,
            current_balance=Decimal(str(a["bal"])),
            sort_order=i + 1,
        )
        db.add(acc)

    db.commit()
    print(f"已创建 {len(accounts)} 个银行账户")


def init_demo_finance_data(db: Session):
    """初始化演示财务数据 - v0.2.0 增强版
    3个项目各有完整的收入/成本/收付款凭证，人材机结构符合行业参考值
    """
    existing = db.query(AccSubjectBalance).filter(AccSubjectBalance.company_id == 1).count()
    if existing > 0:
        print(f"财务数据已存在 ({existing} 条)，跳过")
        return

    today = date.today()
    period = today.strftime("%Y-%m")

    # 先建科目映射（演示用，直接用标准科目编码）
    from app.models.config import CfgSubjectMapping
    std_subjects = db.query(CfgStdSubject).filter(CfgStdSubject.company_id == 0).all()
    # 映射所有标准科目
    for s in std_subjects:
        m = CfgSubjectMapping(
            company_id=1,
            source_code=s.subject_code,
            source_name=s.subject_name,
            source_full_name=s.subject_name,
            std_subject_id=s.id,
            std_subject_code=s.subject_code,
            std_subject_name=s.subject_name,
            match_type="auto",
            match_confidence=Decimal("100"),
            is_mapped=True,
        )
        db.add(m)
    db.commit()

    # 找到标准科目ID
    std_by_code = {s.subject_code: s.id for s in std_subjects}

    # ========== 演示凭证（按项目组织，人材机比例符合行业参考） ==========
    # 项目1：科技园区办公楼（房建）- 人工30% 材料60% 机械10%
    # 项目2：市政道路改造（市政）- 人工20% 材料55% 机械25%
    # 项目3：产业园精装修（装修）- 人工40% 材料55% 机械5%

    # 本月各项目数据（2026年7月）
    # 房建项目：本月收入580万，成本约493万（毛利率15%）
    #   - 人工费：493 × 30% ≈ 148万
    #   - 材料费：493 × 60% ≈ 296万
    #   - 机械费：493 × 10% ≈ 49万
    # 市政项目：本月收入220万，成本约187万（毛利率15%）
    #   - 人工费：187 × 20% ≈ 37万
    #   - 材料费：187 × 55% ≈ 103万
    #   - 机械费：187 × 25% ≈ 47万
    # 装修项目：本月收入180万，成本约153万（毛利率15%）
    #   - 人工费：153 × 40% ≈ 61万
    #   - 材料费：153 × 55% ≈ 84万
    #   - 机械费：153 × 5% ≈ 8万

    vouchers_demo = [
        # ===== 房建项目：科技园区办公楼 =====
        # 1. 确认收入（开票口径）
        {
            "no": "记-07-001", "date": f"{period}-05",
            "summary": "确认科技园区办公楼项目工程进度款（第3期）",
            "items": [
                {"code": "1122", "name": "应收账款", "debit": 5800000, "credit": 0,
                 "aux_project": "苏州工业园区科技园区办公楼项目", "aux_customer": "苏州科技发展有限公司"},
                {"code": "6001", "name": "主营业务收入", "debit": 0, "credit": 5800000,
                 "aux_project": "苏州工业园区科技园区办公楼项目"},
            ]
        },
        # 2. 工程结算（结算口径）
        {
            "no": "记-07-002", "date": f"{period}-05",
            "summary": "科技园区办公楼项目工程结算",
            "items": [
                {"code": "1122", "name": "应收账款", "debit": 5800000, "credit": 0,
                 "aux_project": "苏州工业园区科技园区办公楼项目", "aux_customer": "苏州科技发展有限公司"},
                {"code": "5402", "name": "工程结算", "debit": 0, "credit": 5800000,
                 "aux_project": "苏州工业园区科技园区办公楼项目"},
            ]
        },
        # 3. 人工费
        {
            "no": "记-07-003", "date": f"{period}-08",
            "summary": "计提科技园区项目7月人工费",
            "items": [
                {"code": "54010101", "name": "人工费", "debit": 1480000, "credit": 0,
                 "aux_project": "苏州工业园区科技园区办公楼项目"},
                {"code": "2211", "name": "应付职工薪酬", "debit": 0, "credit": 1480000},
            ]
        },
        # 4. 材料费
        {
            "no": "记-07-004", "date": f"{period}-10",
            "summary": "科技园区项目购入钢材水泥等材料",
            "items": [
                {"code": "54010102", "name": "材料费", "debit": 2960000, "credit": 0,
                 "aux_project": "苏州工业园区科技园区办公楼项目"},
                {"code": "2202", "name": "应付账款", "debit": 0, "credit": 2960000,
                 "aux_project": "苏州工业园区科技园区办公楼项目", "aux_supplier": "苏州建材集团有限公司"},
            ]
        },
        # 5. 机械费
        {
            "no": "记-07-005", "date": f"{period}-12",
            "summary": "科技园区项目塔吊施工电梯租赁费",
            "items": [
                {"code": "54010103", "name": "机械使用费", "debit": 490000, "credit": 0,
                 "aux_project": "苏州工业园区科技园区办公楼项目"},
                {"code": "2202", "name": "应付账款", "debit": 0, "credit": 490000,
                 "aux_project": "苏州工业园区科技园区办公楼项目", "aux_supplier": "苏州建工机械租赁有限公司"},
            ]
        },
        # 6. 收到工程款
        {
            "no": "记-07-006", "date": f"{period}-15",
            "summary": "收科技园区项目第2期进度款",
            "items": [
                {"code": "1002", "name": "银行存款", "debit": 4500000, "credit": 0},
                {"code": "1122", "name": "应收账款", "debit": 0, "credit": 4500000,
                 "aux_project": "苏州工业园区科技园区办公楼项目", "aux_customer": "苏州科技发展有限公司"},
            ]
        },
        # 7. 支付材料款
        {
            "no": "记-07-007", "date": f"{period}-18",
            "summary": "支付苏州建材集团材料款",
            "items": [
                {"code": "2202", "name": "应付账款", "debit": 2000000, "credit": 0,
                 "aux_supplier": "苏州建材集团有限公司"},
                {"code": "1002", "name": "银行存款", "debit": 0, "credit": 2000000},
            ]
        },

        # ===== 市政项目：市政道路改造 =====
        # 8. 确认收入
        {
            "no": "记-07-008", "date": f"{period}-06",
            "summary": "确认市政道路改造项目工程进度款",
            "items": [
                {"code": "1122", "name": "应收账款", "debit": 2200000, "credit": 0,
                 "aux_project": "吴中区市政道路改造项目", "aux_customer": "吴中区市政公用局"},
                {"code": "6001", "name": "主营业务收入", "debit": 0, "credit": 2200000,
                 "aux_project": "吴中区市政道路改造项目"},
            ]
        },
        # 9. 工程结算
        {
            "no": "记-07-009", "date": f"{period}-06",
            "summary": "市政道路改造项目工程结算",
            "items": [
                {"code": "1122", "name": "应收账款", "debit": 2200000, "credit": 0,
                 "aux_project": "吴中区市政道路改造项目", "aux_customer": "吴中区市政公用局"},
                {"code": "5402", "name": "工程结算", "debit": 0, "credit": 2200000,
                 "aux_project": "吴中区市政道路改造项目"},
            ]
        },
        # 10. 人工费
        {
            "no": "记-07-010", "date": f"{period}-08",
            "summary": "计提市政道路项目7月人工费",
            "items": [
                {"code": "54010101", "name": "人工费", "debit": 374000, "credit": 0,
                 "aux_project": "吴中区市政道路改造项目"},
                {"code": "2211", "name": "应付职工薪酬", "debit": 0, "credit": 374000},
            ]
        },
        # 11. 材料费（沥青、砂石、管材）
        {
            "no": "记-07-011", "date": f"{period}-10",
            "summary": "市政道路项目购入沥青砂石等材料",
            "items": [
                {"code": "54010102", "name": "材料费", "debit": 1028500, "credit": 0,
                 "aux_project": "吴中区市政道路改造项目"},
                {"code": "2202", "name": "应付账款", "debit": 0, "credit": 1028500,
                 "aux_project": "吴中区市政道路改造项目", "aux_supplier": "苏州市政材料供应公司"},
            ]
        },
        # 12. 机械费（压路机、挖掘机、摊铺机）
        {
            "no": "记-07-012", "date": f"{period}-12",
            "summary": "市政道路项目工程机械租赁费",
            "items": [
                {"code": "54010103", "name": "机械使用费", "debit": 467500, "credit": 0,
                 "aux_project": "吴中区市政道路改造项目"},
                {"code": "2202", "name": "应付账款", "debit": 0, "credit": 467500,
                 "aux_project": "吴中区市政道路改造项目", "aux_supplier": "苏州路桥机械租赁有限公司"},
            ]
        },
        # 13. 收到工程款
        {
            "no": "记-07-013", "date": f"{period}-20",
            "summary": "收市政道路项目进度款",
            "items": [
                {"code": "1002", "name": "银行存款", "debit": 1800000, "credit": 0},
                {"code": "1122", "name": "应收账款", "debit": 0, "credit": 1800000,
                 "aux_project": "吴中区市政道路改造项目", "aux_customer": "吴中区市政公用局"},
            ]
        },

        # ===== 装修项目：产业园精装修 =====
        # 14. 确认收入
        {
            "no": "记-07-014", "date": f"{period}-08",
            "summary": "确认产业园精装修项目进度款",
            "items": [
                {"code": "1122", "name": "应收账款", "debit": 1800000, "credit": 0,
                 "aux_project": "高新区产业园精装修工程", "aux_customer": "苏州高新产业园运营公司"},
                {"code": "6001", "name": "主营业务收入", "debit": 0, "credit": 1800000,
                 "aux_project": "高新区产业园精装修工程"},
            ]
        },
        # 15. 工程结算
        {
            "no": "记-07-015", "date": f"{period}-08",
            "summary": "产业园精装修项目工程结算",
            "items": [
                {"code": "1122", "name": "应收账款", "debit": 1800000, "credit": 0,
                 "aux_project": "高新区产业园精装修工程", "aux_customer": "苏州高新产业园运营公司"},
                {"code": "5402", "name": "工程结算", "debit": 0, "credit": 1800000,
                 "aux_project": "高新区产业园精装修工程"},
            ]
        },
        # 16. 人工费（装修工人、木工、油漆工）
        {
            "no": "记-07-016", "date": f"{period}-10",
            "summary": "计提精装修项目7月人工费",
            "items": [
                {"code": "54010101", "name": "人工费", "debit": 612000, "credit": 0,
                 "aux_project": "高新区产业园精装修工程"},
                {"code": "2211", "name": "应付职工薪酬", "debit": 0, "credit": 612000},
            ]
        },
        # 17. 材料费（地板、瓷砖、涂料、灯具）
        {
            "no": "记-07-017", "date": f"{period}-15",
            "summary": "精装修项目购入装饰材料",
            "items": [
                {"code": "54010102", "name": "材料费", "debit": 841500, "credit": 0,
                 "aux_project": "高新区产业园精装修工程"},
                {"code": "2202", "name": "应付账款", "debit": 0, "credit": 841500,
                 "aux_project": "高新区产业园精装修工程", "aux_supplier": "苏州装饰材料有限公司"},
            ]
        },
        # 18. 机械费（小型机具、电动工具）
        {
            "no": "记-07-018", "date": f"{period}-18",
            "summary": "精装修项目小型机具使用费",
            "items": [
                {"code": "54010103", "name": "机械使用费", "debit": 76500, "credit": 0,
                 "aux_project": "高新区产业园精装修工程"},
                {"code": "1002", "name": "银行存款", "debit": 0, "credit": 76500},
            ]
        },
        # 19. 收到工程款
        {
            "no": "记-07-019", "date": f"{period}-25",
            "summary": "收精装修项目进度款",
            "items": [
                {"code": "1002", "name": "银行存款", "debit": 1500000, "credit": 0},
                {"code": "1122", "name": "应收账款", "debit": 0, "credit": 1500000,
                 "aux_project": "高新区产业园精装修工程", "aux_customer": "苏州高新产业园运营公司"},
            ]
        },

        # ===== 公共费用 =====
        # 20. 支付管理人员工资
        {
            "no": "记-07-020", "date": f"{period}-22",
            "summary": "支付7月管理人员工资",
            "items": [
                {"code": "6602", "name": "管理费用", "debit": 280000, "credit": 0},
                {"code": "2211", "name": "应付职工薪酬", "debit": 0, "credit": 280000},
            ]
        },
        # 21. 支付工资
        {
            "no": "记-07-021", "date": f"{period}-25",
            "summary": "发放7月工资",
            "items": [
                {"code": "2211", "name": "应付职工薪酬", "debit": 1500000, "credit": 0},
                {"code": "1002", "name": "银行存款", "debit": 0, "credit": 1500000},
            ]
        },
        # 22. 支付银行手续费
        {
            "no": "记-07-022", "date": f"{period}-28",
            "summary": "支付银行手续费及利息",
            "items": [
                {"code": "6603", "name": "财务费用", "debit": 35000, "credit": 0},
                {"code": "1002", "name": "银行存款", "debit": 0, "credit": 35000},
            ]
        },
        # 23. 结转主营业务成本（按收入匹配）
        {
            "no": "记-07-023", "date": f"{period}-31",
            "summary": "结转7月主营业务成本",
            "items": [
                {"code": "6401", "name": "主营业务成本", "debit": 8320000, "credit": 0},
                {"code": "54010101", "name": "人工费", "debit": 0, "credit": 2466000},
                {"code": "54010102", "name": "材料费", "debit": 0, "credit": 4829500},
                {"code": "54010103", "name": "机械使用费", "debit": 0, "credit": 1024500},
            ]
        },
        # 24. 工程施工与工程结算对冲
        {
            "no": "记-07-024", "date": f"{period}-31",
            "summary": "工程施工与工程结算对冲",
            "items": [
                {"code": "5402", "name": "工程结算", "debit": 9800000, "credit": 0},
                {"code": "540101", "name": "合同成本", "debit": 0, "credit": 8320000},
                {"code": "6001", "name": "主营业务收入", "debit": 0, "credit": 1480000},  # 合同毛利
            ]
        },
    ]

    voucher_count = 0
    item_count = 0
    for v in vouchers_demo:
        voucher = AccVoucher(
            company_id=1,
            batch_id=1,
            voucher_no=v["no"],
            voucher_date=datetime.strptime(v["date"], "%Y-%m-%d").date(),
            period=period,
            summary=v["summary"],
            total_debit=Decimal(str(sum(i["debit"] for i in v["items"]))),
            total_credit=Decimal(str(sum(i["credit"] for i in v["items"]))),
        )
        db.add(voucher)
        db.flush()
        voucher_count += 1

        for line_no, item in enumerate(v["items"], 1):
            v_item = AccVoucherItem(
                company_id=1,
                voucher_id=voucher.id,
                voucher_date=voucher.voucher_date,
                period=period,
                line_no=line_no,
                subject_code=item["code"],
                subject_name=item["name"],
                std_subject_id=std_by_code.get(item["code"]),
                std_subject_code=item["code"] if item["code"] in std_by_code else None,
                summary=v["summary"],
                debit=Decimal(str(item["debit"])),
                credit=Decimal(str(item["credit"])),
                aux_project=item.get("aux_project"),
                aux_customer=item.get("aux_customer"),
                aux_supplier=item.get("aux_supplier"),
            )
            db.add(v_item)
            item_count += 1

    db.commit()
    print(f"已创建 {voucher_count} 张演示凭证，{item_count} 条分录")
    print(f"  - 房建项目：科技园区办公楼（580万收入，人材机30/60/10）")
    print(f"  - 市政项目：市政道路改造（220万收入，人材机20/55/25）")
    print(f"  - 装修项目：产业园精装修（180万收入，人材机40/55/5）")

    # 补充科目余额表（从凭证汇总生成）
    _generate_balance_from_vouchers(db, period, std_by_code)


def _generate_balance_from_vouchers(db: Session, period: str, std_by_code: dict):
    """从凭证汇总生成科目余额表"""
    from app.models.finance import AccSubjectBalance

    # 汇总各科目借贷发生额
    from sqlalchemy import func
    from app.models.finance import AccVoucherItem

    rows = db.query(
        AccVoucherItem.subject_code,
        AccVoucherItem.subject_name,
        AccVoucherItem.std_subject_code,
        func.sum(AccVoucherItem.debit).label("total_debit"),
        func.sum(AccVoucherItem.credit).label("total_credit"),
    ).filter(
        AccVoucherItem.company_id == 1,
        AccVoucherItem.period == period,
    ).group_by(
        AccVoucherItem.subject_code,
        AccVoucherItem.subject_name,
        AccVoucherItem.std_subject_code,
    ).all()

    # 模拟期初余额（让数据更真实）
    opening_balances = {
        "1001": (50000, 0),      # 库存现金：期初借方5万
        "1002": (6500000, 0),    # 银行存款：期初借方650万
        "1122": (25000000, 0),   # 应收账款：期初借方2500万
        "2202": (0, 12000000),   # 应付账款：期初贷方1200万
        "2211": (0, 800000),     # 应付职工薪酬：期初贷方80万
        "5401": (30000000, 0),   # 工程施工：期初借方3000万
        "5402": (0, 28000000),   # 工程结算：期初贷方2800万
    }

    count = 0
    for row in rows:
        code = row.subject_code
        name = row.subject_name
        current_debit = float(row.total_debit or 0)
        current_credit = float(row.total_credit or 0)

        # 期初余额
        open_debit, open_credit = opening_balances.get(code, (0, 0))

        # 期末余额
        if open_debit + current_debit >= open_credit + current_credit:
            end_debit = open_debit + current_debit - open_credit - current_credit
            end_credit = 0
        else:
            end_debit = 0
            end_credit = open_credit + current_credit - open_debit - current_debit

        bal = AccSubjectBalance(
            company_id=1,
            batch_id=1,
            period=period,
            subject_code=code,
            subject_name=name,
            subject_full_name=name,
            std_subject_id=std_by_code.get(code),
            std_subject_code=code if code in std_by_code else None,
            begin_debit=Decimal(str(open_debit)),
            begin_credit=Decimal(str(open_credit)),
            current_debit=Decimal(str(current_debit)),
            current_credit=Decimal(str(current_credit)),
            end_debit=Decimal(str(end_debit)),
            end_credit=Decimal(str(end_credit)),
            year_debit=Decimal(str(current_debit * 6)),  # 假设半年数据
            year_credit=Decimal(str(current_credit * 6)),
        )
        db.add(bal)
        count += 1

    db.commit()
    print(f"已生成 {count} 条科目余额数据")


def main():
    print("=" * 60)
    print("建税盾·建筑经营管理报表系统 - 数据初始化")
    print("=" * 60)

    # 建表
    Base.metadata.create_all(bind=engine)
    print("数据库表结构已创建/更新")

    db = SessionLocal()
    try:
        init_std_subjects(db)
        init_company_and_user(db)
        init_demo_projects(db)
        init_demo_bank_accounts(db)
        init_demo_finance_data(db)

        print("\n" + "=" * 60)
        print("✅ 初始化完成！")
        print("演示账号: boss / 123456 (老板视角)")
        print("         finance / 123456 (财务视角)")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
