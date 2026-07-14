<template>
  <div class="tax-burden-page">
    <div class="page-header">
      <div>
        <div class="page-title">税负率与缺票分析</div>
        <div class="page-subtitle">实时监控税负健康度，预警缺票风险</div>
      </div>
      <div class="header-tools">
        <el-select v-model="selectedPeriod" size="small" style="width: 140px">
          <el-option label="2026年6月" value="2026-06" />
          <el-option label="2026年5月" value="2026-05" />
          <el-option label="2026年累计" value="2026-ytd" />
        </el-select>
      </div>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metric-cards">
      <div class="metric-card" :class="vatBurdenStatus">
        <div class="metric-header">
          <span class="metric-icon">📈</span>
          <span class="metric-title">增值税税负率</span>
          <el-tag :type="vatBurdenTagType" size="small">{{ vatBurdenStatusText }}</el-tag>
        </div>
        <div class="metric-value">{{ vatBurdenRate }}%</div>
        <div class="metric-compare">
          行业参考: {{ industryVatReference }}%
          <span :class="vatDiffClass">
            {{ vatDiff > 0 ? '+' : '' }}{{ vatDiff }}%
          </span>
        </div>
        <div class="metric-bar">
          <div class="bar-track">
            <div class="bar-fill vat-bar" :style="{ width: Math.min(vatBurdenRate / industryVatReference * 50 + 50, 100) + '%' }"></div>
          </div>
          <div class="bar-markers">
            <span class="marker low">偏低</span>
            <span class="marker mid">正常</span>
            <span class="marker high">偏高</span>
          </div>
        </div>
      </div>

      <div class="metric-card" :class="incomeTaxStatus">
        <div class="metric-header">
          <span class="metric-icon">💼</span>
          <span class="metric-title">所得税税负率</span>
          <el-tag :type="incomeTaxTagType" size="small">{{ incomeTaxStatusText }}</el-tag>
        </div>
        <div class="metric-value">{{ incomeTaxRate }}%</div>
        <div class="metric-compare">
          行业参考: {{ industryIncomeTaxReference }}%
          <span :class="incomeTaxDiffClass">
            {{ incomeTaxDiff > 0 ? '+' : '' }}{{ incomeTaxDiff }}%
          </span>
        </div>
        <div class="metric-bar">
          <div class="bar-track">
            <div class="bar-fill income-bar" :style="{ width: Math.min(incomeTaxRate / industryIncomeTaxReference * 50 + 50, 100) + '%' }"></div>
          </div>
          <div class="bar-markers">
            <span class="marker low">偏低</span>
            <span class="marker mid">正常</span>
            <span class="marker high">偏高</span>
          </div>
        </div>
      </div>

      <div class="metric-card invoice-card">
        <div class="metric-header">
          <span class="metric-icon">🧾</span>
          <span class="metric-title">进项发票缺口</span>
          <el-tag type="danger" size="small">预警</el-tag>
        </div>
        <div class="metric-value warning-value">{{ formatMoney(inputTaxShortfall) }}</div>
        <div class="metric-compare">
          需进项税: {{ formatMoney(theoreticalInputTax) }}
          已取得: {{ formatMoney(actualInputTax) }}
        </div>
        <div class="metric-bar">
          <div class="bar-track">
            <div class="bar-fill input-bar" :style="{ width: inputTaxCoverage + '%' }"></div>
          </div>
          <div class="bar-completion">
            覆盖率 {{ inputTaxCoverage.toFixed(1) }}%
          </div>
        </div>
      </div>

      <div class="metric-card cost-card">
        <div class="metric-header">
          <span class="metric-icon">📋</span>
          <span class="metric-title">成本票缺口</span>
          <el-tag :type="costShortfallTagType" size="small">{{ costShortfallText }}</el-tag>
        </div>
        <div class="metric-value">{{ formatMoney(costInvoiceShortfall) }}</div>
        <div class="metric-compare">
          需成本票: {{ formatMoney(theoreticalCostInvoice) }}
          已取得: {{ formatMoney(actualCostInvoice) }}
        </div>
        <div class="metric-bar">
          <div class="bar-track">
            <div class="bar-fill cost-bar" :style="{ width: costInvoiceCoverage + '%' }"></div>
          </div>
          <div class="bar-completion">
            覆盖率 {{ costInvoiceCoverage.toFixed(1) }}%
          </div>
        </div>
      </div>
    </div>

    <div class="content-row">
      <!-- 左侧：缺票明细分析 -->
      <div class="panel detail-panel">
        <div class="panel-title">
          <span class="title-icon">📊</span>
          缺票明细分析
        </div>

        <div class="category-tabs">
          <div
            v-for="tab in tabs"
            :key="tab.key"
            class="tab-item"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </div>
        </div>

        <div class="shortfall-list">
          <div class="shortfall-header">
            <span class="col-name">类别</span>
            <span class="col-theory">理论应取</span>
            <span class="col-actual">实际取得</span>
            <span class="col-gap">缺口</span>
            <span class="col-risk">风险</span>
          </div>
          <div
            v-for="item in currentShortfallList"
            :key="item.name"
            class="shortfall-item"
          >
            <span class="col-name">{{ item.name }}</span>
            <span class="col-theory">{{ formatMoney(item.theoretical) }}</span>
            <span class="col-actual">{{ formatMoney(item.actual) }}</span>
            <span class="col-gap" :class="item.gap > 0 ? 'gap-warning' : 'gap-ok'">
              {{ item.gap > 0 ? formatMoney(item.gap) : '-' }}
            </span>
            <span class="col-risk">
              <el-tag :type="item.riskLevel" size="small">{{ item.riskText }}</el-tag>
            </span>
          </div>
        </div>
      </div>

      <!-- 右侧：风险提示与建议 -->
      <div class="panel risk-panel">
        <div class="panel-title">
          <span class="title-icon">⚠️</span>
          风险提示与建议
        </div>

        <div class="risk-list">
          <div class="risk-item high-risk">
            <div class="risk-header">
              <el-tag type="danger" size="small">高风险</el-tag>
              <span class="risk-title">进项票缺口较大</span>
            </div>
            <div class="risk-desc">
              当前进项票缺口 {{ formatMoney(inputTaxShortfall) }} 元，增值税税负率偏高，
              建议尽快梳理采购链条，确认未开票供应商，及时催要发票。
            </div>
          </div>

          <div class="risk-item medium-risk">
            <div class="risk-header">
              <el-tag type="warning" size="small">中风险</el-tag>
              <span class="risk-title">材料费发票不足</span>
            </div>
            <div class="risk-desc">
              材料类成本票缺口较大，可能存在供应商未及时开票或白条入账情况，
              建议重点排查钢材、混凝土等大宗材料采购。
            </div>
          </div>

          <div class="risk-item medium-risk">
            <div class="risk-header">
              <el-tag type="warning" size="small">中风险</el-tag>
              <span class="risk-title">人工成本占比偏高</span>
            </div>
            <div class="risk-desc">
              人工费占比高于行业均值5个百分点，需关注是否存在劳务发票不足、
              工资未足额申报个税等问题。
            </div>
          </div>

          <div class="risk-item low-risk">
            <div class="risk-header">
              <el-tag type="success" size="small">正常</el-tag>
              <span class="risk-title">机械费基本匹配</span>
            </div>
            <div class="risk-desc">
              机械费发票取得情况良好，与行业参考值基本一致。
            </div>
          </div>
        </div>

        <div class="action-suggestion">
          <div class="suggestion-title">💡 操作建议</div>
          <ul class="suggestion-list">
            <li>月底前完成供应商发票催收，重点盯材料供应商</li>
            <li>核查劳务班组结算情况，确保劳务发票及时取得</li>
            <li>评估税负率偏高原因，是行业特性还是管理问题</li>
            <li>建立发票台账，实时跟踪进项票取得进度</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 分项目税负对比 -->
    <div class="panel project-compare-panel">
      <div class="panel-title">
        <span class="title-icon">🏗️</span>
        分项目税负对比
      </div>
      <table class="compare-table">
        <thead>
          <tr>
            <th>项目名称</th>
            <th>不含税收入</th>
            <th>应交增值税</th>
            <th>增值税税负</th>
            <th>应交所得税</th>
            <th>所得税税负</th>
            <th>进项缺口</th>
            <th>综合评价</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="project in projectTaxList" :key="project.id">
            <td class="project-name">{{ project.name }}</td>
            <td>{{ formatMoney(project.income) }}</td>
            <td>{{ formatMoney(project.vat) }}</td>
            <td>
              <span :class="project.vat_rate > industryVatReference + 1 ? 'rate-high' : project.vat_rate < industryVatReference - 1 ? 'rate-low' : 'rate-normal'">
                {{ project.vat_rate.toFixed(2) }}%
              </span>
            </td>
            <td>{{ formatMoney(project.income_tax) }}</td>
            <td>
              <span :class="project.income_tax_rate > industryIncomeTaxReference + 0.5 ? 'rate-high' : project.income_tax_rate < industryIncomeTaxReference - 0.5 ? 'rate-low' : 'rate-normal'">
                {{ project.income_tax_rate.toFixed(2) }}%
              </span>
            </td>
            <td class="gap-cell">
              <span :class="project.input_gap > 100000 ? 'gap-warning' : 'gap-ok'">
                {{ formatMoney(project.input_gap) }}
              </span>
            </td>
            <td>
              <el-tag :type="project.overall_risk" size="small">{{ project.overall_text }}</el-tag>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const selectedPeriod = ref('2026-06')
const activeTab = ref('input')

const tabs = [
  { key: 'input', label: '进项税明细' },
  { key: 'cost', label: '成本票明细' },
]

// 行业参考值（建筑行业）
const industryVatReference = 2.5  // 增值税税负率参考
const industryIncomeTaxReference = 1.5  // 所得税税负率参考

// 模拟数据
const vatBurdenRate = 3.2
const incomeTaxRate = 1.8

const vatDiff = (vatBurdenRate - industryVatReference).toFixed(2)
const incomeTaxDiff = (incomeTaxRate - industryIncomeTaxReference).toFixed(2)

const vatBurdenStatus = computed(() => {
  if (vatBurdenRate > industryVatReference + 1) return 'status-high'
  if (vatBurdenRate < industryVatReference - 1) return 'status-low'
  return 'status-normal'
})

const vatBurdenTagType = computed(() => {
  if (vatBurdenRate > industryVatReference + 1) return 'warning'
  if (vatBurdenRate < industryVatReference - 1) return 'danger'
  return 'success'
})

const vatBurdenStatusText = computed(() => {
  if (vatBurdenRate > industryVatReference + 1) return '偏高'
  if (vatBurdenRate < industryVatReference - 1) return '偏低'
  return '正常'
})

const vatDiffClass = computed(() => {
  if (vatBurdenRate > industryVatReference) return 'diff-up'
  return 'diff-down'
})

const incomeTaxStatus = computed(() => {
  if (incomeTaxRate > industryIncomeTaxReference + 0.5) return 'status-high'
  if (incomeTaxRate < industryIncomeTaxReference - 0.5) return 'status-low'
  return 'status-normal'
})

const incomeTaxTagType = computed(() => {
  if (incomeTaxRate > industryIncomeTaxReference + 0.5) return 'warning'
  if (incomeTaxRate < industryIncomeTaxReference - 0.5) return 'danger'
  return 'success'
})

const incomeTaxStatusText = computed(() => {
  if (incomeTaxRate > industryIncomeTaxReference + 0.5) return '偏高'
  if (incomeTaxRate < industryIncomeTaxReference - 0.5) return '偏低'
  return '正常'
})

const incomeTaxDiffClass = computed(() => {
  if (incomeTaxRate > industryIncomeTaxReference) return 'diff-up'
  return 'diff-down'
})

// 缺票数据
const theoreticalInputTax = 825688.07  // 理论应取得进项税
const actualInputTax = 580000  // 实际取得进项税
const inputTaxShortfall = theoreticalInputTax - actualInputTax  // 进项税缺口
const inputTaxCoverage = (actualInputTax / theoreticalInputTax * 100)

const theoreticalCostInvoice = 8590825.69  // 理论应取得成本票（不含税）
const actualCostInvoice = 6800000  // 实际取得
const costInvoiceShortfall = theoreticalCostInvoice - actualCostInvoice
const costInvoiceCoverage = (actualCostInvoice / theoreticalCostInvoice * 100)

const costShortfallTagType = computed(() => {
  if (costInvoiceCoverage < 70) return 'danger'
  if (costInvoiceCoverage < 85) return 'warning'
  return 'success'
})

const costShortfallText = computed(() => {
  if (costInvoiceCoverage < 70) return '缺口大'
  if (costInvoiceCoverage < 85) return '有缺口'
  return '基本充足'
})

// 进项税明细
const inputTaxDetail = [
  { name: '材料类（13%）', theoretical: 520000, actual: 380000, gap: 140000, riskLevel: 'danger', riskText: '高风险' },
  { name: '机械类（13%）', theoretical: 85000, actual: 80000, gap: 5000, riskLevel: 'success', riskText: '正常' },
  { name: '运输类（9%）', theoretical: 45000, actual: 30000, gap: 15000, riskLevel: 'warning', riskText: '关注' },
  { name: '劳务类（3%/6%）', theoretical: 120000, actual: 60000, gap: 60000, riskLevel: 'warning', riskText: '关注' },
  { name: '其他服务类', theoretical: 55688, actual: 30000, gap: 25688, riskLevel: 'warning', riskText: '关注' },
]

// 成本票明细
const costInvoiceDetail = [
  { name: '材料费', theoretical: 5100000, actual: 3800000, gap: 1300000, riskLevel: 'danger', riskText: '高风险' },
  { name: '人工费', theoretical: 2550000, actual: 2000000, gap: 550000, riskLevel: 'warning', riskText: '关注' },
  { name: '机械费', theoretical: 510000, actual: 480000, gap: 30000, riskLevel: 'success', riskText: '正常' },
  { name: '分包费', theoretical: 300000, actual: 280000, gap: 20000, riskLevel: 'success', riskText: '正常' },
  { name: '其他费用', theoretical: 130825, actual: 110000, gap: 20825, riskLevel: 'info', riskText: '正常' },
]

const currentShortfallList = computed(() => {
  return activeTab.value === 'input' ? inputTaxDetail : costInvoiceDetail
})

// 分项目税负对比
const projectTaxList = [
  {
    id: 1,
    name: '苏州工业园区科技园区办公楼项目',
    income: 18500000,
    vat: 592000,
    vat_rate: 3.2,
    income_tax: 277500,
    income_tax_rate: 1.5,
    input_gap: 145000,
    overall_risk: 'warning',
    overall_text: '关注',
  },
  {
    id: 2,
    name: '吴中区市政道路改造项目',
    income: 7200000,
    vat: 180000,
    vat_rate: 2.5,
    income_tax: 108000,
    income_tax_rate: 1.5,
    input_gap: 35000,
    overall_risk: 'success',
    overall_text: '正常',
  },
  {
    id: 3,
    name: '高新区产业园精装修工程',
    income: 3600000,
    vat: 144000,
    vat_rate: 4.0,
    income_tax: 72000,
    income_tax_rate: 2.0,
    input_gap: 95000,
    overall_risk: 'danger',
    overall_text: '预警',
  },
  {
    id: 4,
    name: '相城区人才公寓一期工程',
    income: 32000000,
    vat: 800000,
    vat_rate: 2.5,
    income_tax: 480000,
    income_tax_rate: 1.5,
    input_gap: 50000,
    overall_risk: 'success',
    overall_text: '正常',
  },
]

function formatMoney(val) {
  if (val === undefined || val === null) return '0.00'
  const num = parseFloat(val)
  if (Math.abs(num) >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>

<style scoped>
.tax-burden-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: bold;
  color: #0a1f44;
  margin-bottom: 8px;
}

.page-subtitle {
  color: #909399;
  font-size: 14px;
}

.metric-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.metric-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-top: 4px solid #409eff;
}

.metric-card.status-high {
  border-top-color: #e6a23c;
}

.metric-card.status-low {
  border-top-color: #f56c6c;
}

.metric-card.status-normal {
  border-top-color: #67c23a;
}

.metric-card.invoice-card {
  border-top-color: #f56c6c;
}

.metric-card.cost-card {
  border-top-color: #c9a24a;
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.metric-icon {
  font-size: 20px;
}

.metric-title {
  font-size: 14px;
  color: #606266;
  flex: 1;
}

.metric-value {
  font-size: 28px;
  font-weight: bold;
  color: #0a1f44;
  margin-bottom: 8px;
}

.metric-value.warning-value {
  color: #f56c6c;
}

.metric-compare {
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.diff-up {
  color: #f56c6c;
  margin-left: 8px;
}

.diff-down {
  color: #67c23a;
  margin-left: 8px;
}

.metric-bar {
  margin-top: 8px;
}

.bar-track {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.vat-bar {
  background: linear-gradient(90deg, #67c23a, #e6a23c, #f56c6c);
}

.income-bar {
  background: linear-gradient(90deg, #67c23a, #e6a23c, #f56c6c);
}

.input-bar {
  background: linear-gradient(90deg, #f56c6c, #e6a23c, #67c23a);
}

.cost-bar {
  background: linear-gradient(90deg, #f56c6c, #e6a23c, #67c23a);
}

.bar-markers {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 11px;
  color: #c0c4cc;
}

.bar-completion {
  text-align: right;
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}

.content-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.detail-panel {
  flex: 1.5;
}

.risk-panel {
  flex: 1;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #0a1f44;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 18px;
}

.category-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.tab-item {
  padding: 10px 20px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.tab-item.active {
  color: #0a1f44;
  font-weight: 600;
  border-bottom-color: #c9a24a;
}

.shortfall-header {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr 1.5fr 1fr;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 6px;
  font-size: 13px;
  color: #909399;
  font-weight: 500;
}

.shortfall-item {
  display: grid;
  grid-template-columns: 2fr 1.5fr 1.5fr 1.5fr 1fr;
  padding: 12px;
  border-bottom: 1px solid #f5f5f5;
  font-size: 14px;
  align-items: center;
}

.shortfall-item:hover {
  background: #fafafa;
}

.col-name {
  color: #303133;
  font-weight: 500;
}

.col-theory,
.col-actual {
  text-align: right;
  color: #606266;
}

.col-gap {
  text-align: right;
  font-weight: 500;
}

.gap-warning {
  color: #f56c6c;
}

.gap-ok {
  color: #67c23a;
}

.col-risk {
  text-align: center;
}

.risk-list {
  margin-bottom: 20px;
}

.risk-item {
  padding: 14px;
  border-radius: 6px;
  margin-bottom: 12px;
  border-left: 4px solid;
}

.risk-item.high-risk {
  background: #fef0f0;
  border-left-color: #f56c6c;
}

.risk-item.medium-risk {
  background: #fdf6ec;
  border-left-color: #e6a23c;
}

.risk-item.low-risk {
  background: #f0f9eb;
  border-left-color: #67c23a;
}

.risk-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.risk-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.risk-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.action-suggestion {
  background: linear-gradient(135deg, #ecf5ff 0%, #e8f0fe 100%);
  border-radius: 6px;
  padding: 16px;
}

.suggestion-title {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 10px;
}

.suggestion-list {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.project-compare-panel {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
}

.compare-table th,
.compare-table td {
  padding: 12px 16px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.compare-table th {
  background: #fafafa;
  color: #909399;
  font-weight: 500;
}

.project-name {
  text-align: left !important;
  color: #303133;
  font-weight: 500;
}

.rate-high {
  color: #f56c6c;
  font-weight: 600;
}

.rate-low {
  color: #e6a23c;
  font-weight: 600;
}

.rate-normal {
  color: #67c23a;
}

.gap-cell {
  font-weight: 500;
}
</style>
