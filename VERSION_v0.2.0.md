# 建税盾 v0.2.0 版本说明

**发布日期**：2026-07-13
**版本号**：v0.2.0
**代号**：核心三剑客

---

## 🎯 版本定位

从"财务报表系统"升级为"老板驾驶舱"，聚焦建筑老板最关心的三件事：
1. 每个项目赚不赚钱？→ 项目独立核算
2. 挂靠项目怎么收费？→ 挂靠税费精算
3. 缺多少票、税负高不高？→ 税负率与缺票分析

---

## ✨ 新增功能

### 1. 项目独立核算看板 ⭐ 核心功能

**项目列表页**
- 4个演示项目：房建/市政/装修/人才公寓
- 每个项目展示：合同金额、已开票、已收款、待收款、已发生成本、毛利、毛利率、完工进度
- 顶部汇总卡片：合同总额、累计收入、累计成本、累计毛利、累计收款、整体毛利率
- 收入模式切换：开票口径 / 结算口径 / 完工百分比（三种模式一键切换）
- 点击项目卡片进入详情页

**项目详情页**
- 项目基本信息：名称、编号、状态、项目经理、开工/竣工日期
- 收入分析（三模式切换）
- 成本明细：人材机分包其他分类占比
- 毛利分析：毛利率走势
- 资金情况：已收款/待收款/已付款/待付款
- 发票情况：销项/进项/缺票预警
- 工程施工与工程结算对冲表

**技术实现**
- 后端：`app/services/project_accounting_service.py`
- API：`/api/project-accounting/board`、`/api/project-accounting/detail/{id}`
- 前端：`views/ProjectBoard.vue`、`views/ProjectBoardDetail.vue`

---

### 2. 挂靠税费精算计算器 🔥 杀手级功能

**标准模式**
- 5个核心输入（全部手动可调）：
  - 合同金额（含税）
  - 适用税率（默认9%，支持3%/6%/9%/13%）
  - 挂靠费比例（默认2%）
  - 增值税税负率（默认2.5%）
  - 所得税税负率（默认1.5%）

- 20+项计算输出：
  - 基础数据：不含税金额、销项税额
  - 各项税费：增值税、附加税（城建+教育+地方教育）、企业所得税、印花税、挂靠管理费
  - 汇总：税费合计、合计扣款、实际到手、综合费率
  - 发票需求：需要进项税、需成本票（不含税/含税）、账面利润、分红个税

**先扣后返模式**
- 先按无票最大情况预扣（增值税全额+所得税按25%利润率）
- 再根据提供的进项发票和成本发票计算返还
- 输出：先扣明细、返还明细、实付金额、进项税缺口、成本票缺口
- 目标税负对比：实际税负是否低于目标税负率

**预设场景**
- 一般计税大包（9%税率，2%挂靠费，2.5%增值税负，1.5%所得税负）
- 简易计税（3%税率，3%挂靠费，1%增值税负，1%所得税负）
- 劳务分包（3%税率，5%挂靠费，0.5%增值税负，1%所得税负）

**技术实现**
- 后端：`app/services/tax_calc_service.py`
- API：`/api/tax/affiliated/calculate`、`/api/tax/affiliated/pre-deduct-return`
- 前端：`views/AffiliatedTaxCalc.vue`

---

### 3. 税负率与缺票分析 ⚠️ 风险预警

- **4张核心指标卡**：
  - 增值税税负率：行业参考值对比 + 偏低/正常/偏高状态
  - 所得税税负率：行业参考值对比 + 偏低/正常/偏高状态
  - 进项发票缺口：理论应取 vs 实际取得 + 覆盖率
  - 成本票缺口：理论应取 vs 实际取得 + 覆盖率

- **缺票明细分析**：
  - 进项税明细：材料类/机械类/运输类/劳务类/其他服务类
  - 成本票明细：材料费/人工费/机械费/分包费/其他费用
  - 每项显示：理论应取、实际取得、缺口金额、风险等级

- **风险提示与建议**：
  - 高风险/中风险/正常分级展示
  - 每条风险附带原因分析和操作建议

- **分项目税负对比表**：
  - 每个项目的增值税税负、所得税税负、进项缺口
  - 与行业参考值对比标色
  - 综合评价：正常/关注/预警

**技术实现**
- 前端：`views/TaxBurdenAnalysis.vue`（MVP阶段前端计算，后续接入后端真实数据）

---

### 4. 人材机占比参考库 📚

- 内置7类工程行业参考值：房建、市政、装修、劳务、安装、水利、园林
- 可视化柱状图展示
- 项目实际值与行业参考值对比
- 自动识别异常项（偏差>5%关注，>10%异常）
- 智能分析建议
- 完整对照表一览

**技术实现**
- 后端：`app/services/project_accounting_service.py` → `get_lmr_reference()`
- 前端：`views/LmrReference.vue`

---

### 5. 税检康飞书对接API 📬

- 税检康H5提交检测结果后，自动写入飞书多维表
- 字段映射：手机号、企业名称、联系人、行业、总分、风险等级、维度得分、答题详情
- 未配置飞书时自动降级为模拟提交（不影响用户体验）
- API：`POST /api/taxcheck/submit`

**技术实现**
- 后端：`app/services/feishu_bitable.py` + `app/api/taxcheck.py`
- 配置：环境变量 FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_BITABLE_APP_TOKEN / FEISHU_BITABLE_TABLE_ID

---

## 🔧 专业修复

### 核算逻辑修正（v0.1.0 → v0.2.0）

1. **工程结算科目分类修正**
   - 修复前：5402工程结算归为 income_main（收入类）❌
   - 修复后：归为 cost_settlement（成本类备抵科目）✅
   - 影响：工程结算是工程施工的备抵科目，不是收入

2. **收入确认三模式支持**
   - 开票口径：按开票金额确认收入（小企业实际做法）
   - 结算口径：按工程结算贷方发生额确认收入
   - 完工百分比：完工比例由用户手动输入（内部管理用）

3. **成本结转逻辑优化**
   - 按收入占预计总收入的比例结转成本
   - 工程施工（合同成本+合同毛利）与工程结算对冲逻辑

---

## 📁 文件变更清单

### 后端新增
- `backend/app/models/business_ext.py` - 扩展数据模型（项目核算表、发票汇总表、人材机参考表等）
- `backend/app/services/tax_calc_service.py` - 挂靠税费计算引擎
- `backend/app/services/project_accounting_service.py` - 项目核算服务
- `backend/app/services/feishu_bitable.py` - 飞书多维表服务
- `backend/app/api/tax_calc.py` - 税务计算API
- `backend/app/api/project_accounting.py` - 项目核算API
- `backend/app/api/taxcheck.py` - 税检康提交API

### 后端修改
- `backend/main.py` - 新增路由注册，版本号升级为v0.2.0
- `backend/app/core/config.py` - 新增飞书配置项
- `backend/init_data.py` - 新增演示项目和初始化数据

### 前端新增
- `frontend-vite/src/views/AffiliatedTaxCalc.vue` - 挂靠税费计算器页面
- `frontend-vite/src/views/ProjectBoard.vue` - 项目核算看板列表页
- `frontend-vite/src/views/ProjectBoardDetail.vue` - 项目核算详情页
- `frontend-vite/src/views/TaxBurdenAnalysis.vue` - 税负率与缺票分析页面
- `frontend-vite/src/views/LmrReference.vue` - 人材机参考库页面

### 前端修改
- `frontend-vite/src/router/index.js` - 新增5个页面路由
- `frontend-vite/src/layouts/MainLayout.vue` - 新增菜单项

### 文档
- `README.md` - 更新v0.2.0功能介绍

---

## 🚀 启动方式

```bash
# 后端启动
cd backend
python init_data.py      # 初始化演示数据
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 前端启动
cd frontend-vite
npm install
npm run dev
```

**演示账号**：
- 老板视角：boss / 123456
- 财务视角：finance / 123456

---

## 📋 后续规划（v0.3.0+）

- [ ] 现金流预测（3个月滚动+6个月储备，按银行+可动用/不可动用）
- [ ] 税率变动比价器
- [ ] 混合销售平衡点测算
- [ ] Excel导入驱动（科目余额表+发票汇总表）
- [ ] 挂靠项目风险监控（四流匹配/双方结算/缺票预警）
- [ ] 微信扫码登录
- [ ] 移动端适配

---

## 🔐 财税专业声明

本产品所有税费计算公式均基于现行有效税收政策：
- 增值税：依据《中华人民共和国增值税法》
- 企业所得税：依据《中华人民共和国企业所得税法》
- 附加税：城建税7%+教育费附加3%+地方教育附加2%
- 印花税：建筑安装合同0.03%（购销双方合计0.06%）

计算结果仅供参考，实际纳税以税务机关核定为准。
