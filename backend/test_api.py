"""快速验证后端核心功能"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.report_service import get_dashboard_data, get_project_profit_list, get_cash_daily_report, get_ar_aging_report
from app.services.mapping_service import get_mapping_stats
from app.core.security import verify_password, create_access_token

db = SessionLocal()

print("=" * 50)
print("1. 认证测试")
print("-" * 50)
from app.models.system import SysUser
user = db.query(SysUser).filter(SysUser.username == "boss").first()
print(f"用户: {user.real_name}, 角色: {user.role}")
print(f"密码验证: {verify_password('123456', user.password_hash)}")
token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role})
print(f"Token生成: {token[:50]}...")

print("\n" + "=" * 50)
print("2. 科目映射统计")
print("-" * 50)
stats = get_mapping_stats(db, 1)
print(f"总科目数: {stats['total']}")
print(f"已映射: {stats['mapped']} ({stats['mapping_rate']}%)")
print(f"自动映射: {stats['auto_mapped']}, 手动映射: {stats['manual_mapped']}")

print("\n" + "=" * 50)
print("3. 驾驶舱数据")
print("-" * 50)
dashboard = get_dashboard_data(db, 1)
print(f"期间: {dashboard['period']}")
for ind in dashboard['indicators']:
    print(f"  {ind['name']}: {ind['value']:,.2f} {ind['unit']}")

print("\n" + "=" * 50)
print("4. 项目利润表")
print("-" * 50)
projects = get_project_profit_list(db, 1)
print(f"项目数: {len(projects)}")
for p in projects[:3]:
    print(f"  {p['project_name'][:20]}: 收入{p['income']:,.0f} 成本{p['cost']:,.0f} 利润{p['profit']:,.0f} ({p['profit_rate']}%)")

print("\n" + "=" * 50)
print("5. 资金日报")
print("-" * 50)
cash = get_cash_daily_report(db, 1)
print(f"总余额: {cash['total_balance']:,.2f}")
print(f"当日收入: {cash['daily_income']:,.2f}, 当日支出: {cash['daily_expense']:,.2f}")
for acc in cash['accounts']:
    print(f"  {acc['account_name']}: {acc['balance']:,.2f}")

print("\n" + "=" * 50)
print("6. 应收账龄")
print("-" * 50)
ar = get_ar_aging_report(db, 1)
print(f"应收总额: {ar['total_ar']:,.2f}")
print(f"逾期总额: {ar['overdue_total']:,.2f} ({ar['overdue_rate']}%)")
for k, v in ar['buckets'].items():
    print(f"  {k}: {v:,.2f}")

print("\n✅ 所有核心功能验证通过！")
db.close()
