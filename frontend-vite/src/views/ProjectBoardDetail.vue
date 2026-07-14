<template>
  <div class="project-detail-page">
    <!-- 顶部导航 -->
    <div class="page-header">
      <div class="header-left">
        <el-button type="primary" link @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回项目列表
        </el-button>
        <div class="project-title">
          <span class="title-text">{{ projectInfo.project_name || '项目详情' }}</span>
          <el-tag v-if="projectInfo.status" :type="statusType(projectInfo.status)" size="small">
            {{ statusText(projectInfo.status) }}
          </el-tag>
        </div>
      </div>
      <div class="header-right">
        <el-radio-group v-model="incomeMode" size="small" @change="loadDetail">
          <el-radio-button value="invoicing">开票口径</el-radio-button>
          <el-radio-button value="settlement">结算口径</el-radio-button>
          <el-radio-button value="percentage">完工百分比</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 基本信息 + 核心指标 -->
    <div class="top-section">
      <div class="basic-info-card">
        <div class="card-title">项目基本信息</div>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">客户名称</span>
            <span class="value">{{ projectInfo.customer_name || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">合同金额</span>
            <span class="value">{{ formatMoney(projectInfo.contract_amount) }}</span>
          </div>
          <div class="info-item">
            <span class="label">预算成本</span>
            <span class="value">{{ formatMoney(projectInfo.budget_cost) }}</span>
          </div>
          <div class="info-item">
            <span class="label">项目经理</span>
            <span class="value">{{ projectInfo.manager || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">开工日期</span>
            <span class="value">{{ projectInfo.start_date || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="label">竣工日期</span>
            <span class="value">{{ projectInfo.end_date || '-' }}</span>
          </div>
        </div>
      </div>

      <div class="kpi-cards">
        <div class="kpi-card income">
          <div class="kpi-label">本月收入</div>
          <div class="kpi-value">{{ formatMoney(currentIncome) }}</div>
          <div class="kpi-sub">{{ incomeModeName }}口径</div>
        </div>
        <div class="kpi-card cost">
          <div class="kpi-label">结转成本</div>
          <div class="kpi-value">{{ formatMoney(costDetail?.carryover_cost) }}</div>
          <div class="kpi-sub">与收入匹配</div>
        </div>
        <div class="kpi-card profit">
          <div class="kpi-label">毛利额</div>
          <div class="kpi-value">{{ formatMoney(grossProfit?.amount) }}</div>
          <div class="kpi-sub">毛利率 {{ grossProfit?.rate?.toFixed(1) }}%</div>
        </div>
        <div class="kpi-card cash">
          <div class="kpi-label">净现金流</div>
          <div class="kpi-value" :class="fundInfo?.net_cash_flow >= 0 ? 'positive' : 'negative'">
            {{ formatMoney(fundInfo?.net_cash_flow) }}
          </div>
          <div class="kpi-sub">已收 - 已付</div>
        </div>
      </div>
    </div>

    <!-- 详情Tab -->
    <el-tabs v-model="activeTab" class="detail-tabs">
      <!-- 成本明细 -->
      <el-tab-pane label="成本明细" name="cost">
        <div class="tab-content">
          <div class="cost-structure-card">
            <div class="card-title">成本结构（人材机）</div>
            <div class="cost-chart-row">
              <div class="cost-chart" ref="costChart" style="width: 300px; height: 250px"></div>
              <div class="cost-list">
                <div
                  v-for="item in costDetail?.cost_structure"
                  :key="item.name"
                  class="cost-item"
                >
                  <div class="cost-item-header">
                    <span class="cost-name">{{ item.name }}</span>
                    <span class="cost-amount">{{ formatMoney(item.value) }}</span>
                  </div>
                  <el-progress
                    :percentage="item.ratio"
                    :stroke-width="8"
                    :show-text="false"
                    :color="getCostColor(item.name)"
                  />
                  <div class="cost-ratio">占比 {{ item.ratio?.toFixed(1) }}%</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 人材机对比行业参考 -->
          <div class="lmr-compare-card">
            <div class="card-title">
              与行业参考对比
              <el-select v-model="projectType" size="small" style="width: 140px; margin-left: 12px">
                <el-option label="房建工程" value="房建工程" />
                <el-option label="市政工程" value="市政工程" />
                <el-option label="装修工程" value="装修工程" />
                <el-option label="劳务工程" value="劳务工程" />
                <el-option label="安装工程" value="安装工程" />
                <el-option label="水利工程" value="水利工程" />
                <el-option label="园林工程" value="园林工程" />
              </el-select>
            </div>
            <div class="compare-table">
              <div class="compare-header">
                <span>类别</span>
                <span>项目实际</span>
                <span>行业参考</span>
                <span>差异</span>
              </div>
              <div
                v-for="item in lmrComparison"
                :key="item.name"
                class="compare-row"
              >
                <span class="row-name">{{ item.name }}</span>
                <span>{{ item.project_ratio?.toFixed(1) }}%</span>
                <span>{{ item.reference_ratio?.toFixed(1) }}%</span>
                <span :class="item.diff > 0 ? 'high' : (item.diff < 0 ? 'low' : '')">
                  {{ item.diff > 0 ? '+' : '' }}{{ item.diff?.toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 资金情况 -->
      <el-tab-pane label="资金情况" name="fund">
        <div class="tab-content">
          <div class="fund-cards">
            <div class="fund-card receive">
              <div class="fund-icon">
                <el-icon><Wallet /></el-icon>
              </div>
              <div class="fund-info">
                <div class="fund-label">已收款</div>
                <div class="fund-amount">{{ formatMoney(fundInfo?.received_amount) }}</div>
              </div>
            </div>
            <div class="fund-card pending-receive">
              <div class="fund-icon">
                <el-icon><Money /></el-icon>
              </div>
              <div class="fund-info">
                <div class="fund-label">待收款</div>
                <div class="fund-amount">{{ formatMoney(fundInfo?.pending_receive) }}</div>
              </div>
            </div>
            <div class="fund-card pay">
              <div class="fund-icon">
                <el-icon><CreditCard /></el-icon>
              </div>
              <div class="fund-info">
                <div class="fund-label">已付款</div>
                <div class="fund-amount">{{ formatMoney(fundInfo?.paid_amount) }}</div>
              </div>
            </div>
            <div class="fund-card pending-pay">
              <div class="fund-icon">
                <el-icon><Document /></el-icon>
              </div>
              <div class="fund-info">
                <div class="fund-label">待付款</div>
                <div class="fund-amount">{{ formatMoney(fundInfo?.pending_pay) }}</div>
              </div>
            </div>
          </div>

          <div class="fund-summary-card">
            <div class="card-title">资金分析</div>
            <div class="fund-analysis">
              <div class="analysis-item">
                <span class="label">回款率</span>
                <span class="value">
                  {{ currentIncome > 0 ? ((fundInfo?.received_amount || 0) / currentIncome * 100).toFixed(1) : 0 }}%
                </span>
              </div>
              <div class="analysis-item">
                <span class="label">付款率</span>
                <span class="value">
                  {{ (costDetail?.incurred_cost || 0) > 0 ? ((fundInfo?.paid_amount || 0) / (costDetail?.incurred_cost || 1) * 100).toFixed(1) : 0 }}%
                </span>
              </div>
              <div class="analysis-item">
                <span class="label">资金占用</span>
                <span class="value">
                  {{ formatMoney((costDetail?.incurred_cost || 0) - (fundInfo?.paid_amount || 0)) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 发票情况 -->
      <el-tab-pane label="发票情况" name="invoice">
        <div class="tab-content">
          <div class="invoice-cards">
            <div class="invoice-card output">
              <div class="invoice-label">销项发票</div>
              <div class="invoice-amount">{{ formatMoney(invoiceInfo?.output?.amount_with_tax) }}</div>
              <div class="invoice-sub">
                不含税 {{ formatMoney(invoiceInfo?.output?.amount_no_tax) }}
                税额 {{ formatMoney(invoiceInfo?.output?.tax) }}
              </div>
            </div>
            <div class="invoice-card input">
              <div class="invoice-label">进项发票（估算）</div>
              <div class="invoice-amount">{{ formatMoney(invoiceInfo?.input?.estimated_amount_with_tax) }}</div>
              <div class="invoice-sub">
                税额 {{ formatMoney(invoiceInfo?.input?.estimated_tax) }}
              </div>
            </div>
          </div>

          <!-- 税负率 -->
          <div class="tax-burden-card">
            <div class="card-title">税负率分析</div>
            <div class="burden-items">
              <div class="burden-item">
                <div class="burden-header">
                  <span>增值税税负率</span>
                  <el-tag
                    v-if="invoiceInfo?.tax_burden?.is_high"
                    type="danger"
                    size="small"
                  >偏高</el-tag>
                  <el-tag
                    v-else-if="invoiceInfo?.tax_burden?.is_low"
                    type="warning"
                    size="small"
                  >偏低</el-tag>
                  <el-tag v-else type="success" size="small">正常</el-tag>
                </div>
                <div class="burden-value">
                  <span class="current">{{ invoiceInfo?.tax_burden?.vat_burden?.toFixed(2) }}%</span>
                  <span class="reference">行业参考 {{ invoiceInfo?.tax_burden?.industry_reference }}%</span>
                </div>
                <el-progress
                  :percentage="Math.min(invoiceInfo?.tax_burden?.vat_burden || 0, 10)"
                  :max="10"
                  :stroke-width="10"
                  :show-text="false"
                  color="#c9a24a"
                />
              </div>
            </div>
          </div>

          <!-- 缺票预警 -->
          <div class="missing-invoice-card" v-if="invoiceInfo?.missing_invoice?.warning">
            <el-alert
              title="缺票预警"
              :description="`缺进项税额约 ${formatMoney(invoiceInfo?.missing_invoice?.missing_input_tax)}，建议尽快取得进项发票`"
              type="warning"
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- 工程施工与结算对冲 -->
      <el-tab-pane label="工程结算" name="settlement">
        <div class="tab-content">
          <div class="settlement-card">
            <div class="card-title">工程施工与工程结算对冲</div>
            <div class="settlement-data">
              <div class="settlement-item">
                <div class="settlement-label">工程施工余额</div>
                <div class="settlement-value">{{ formatMoney(constructionSettlement?.construction_balance) }}</div>
                <div class="settlement-sub">合同成本 + 合同毛利</div>
              </div>
              <div class="settlement-arrow">
                <el-icon><ArrowRightBold /></el-icon>
              </div>
              <div class="settlement-item">
                <div class="settlement-label">工程结算余额</div>
                <div class="settlement-value">{{ formatMoney(constructionSettlement?.settlement_balance) }}</div>
                <div class="settlement-sub">已结算金额</div>
              </div>
              <div class="settlement-arrow">=</div>
              <div class="settlement-item result" :class="offsetStatusClass">
                <div class="settlement-label">{{ constructionSettlement?.offset_status }}</div>
                <div class="settlement-value">{{ formatMoney(constructionSettlement?.offset_amount) }}</div>
                <div class="settlement-sub">
                  {{ constructionSettlement?.offset_status === '已完工未结算' ? '相当于存货' : '相当于预收' }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import {
  ArrowLeft, Wallet, Money, CreditCard, Document, ArrowRightBold
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const projectId = ref(route.params.id)
const incomeMode = ref('invoicing')
const activeTab = ref('cost')
const projectType = ref('房建工程')

const projectInfo = ref({})
const costDetail = ref(null)
const grossProfit = ref(null)
const fundInfo = ref(null)
const invoiceInfo = ref(null)
const constructionSettlement = ref(null)
const costChart = ref(null)
let chartInstance = null

const incomeModeName = computed(() => {
  const map = {
    invoicing: '开票',
    settlement: '结算',
    percentage: '完工百分比'
  }
  return map[incomeMode.value] || '开票'
})

const currentIncome = computed(() => {
  // 根据不同模式取对应收入
  return costDetail.value ? (costDetail.value.gross_profit / (costDetail.value.gross_profit_rate / 100 || 1)) : 0
})

const offsetStatusClass = computed(() => {
  return constructionSettlement.value?.offset_status === '已完工未结算' ? 'unsettled' : 'oversettled'
})

// 人材机行业参考数据
const lmrReference = {
  '房建工程': { labor_ratio: 30, material_ratio: 60, machine_ratio: 10 },
  '市政工程': { labor_ratio: 20, material_ratio: 55, machine_ratio: 25 },
  '装修工程': { labor_ratio: 40, material_ratio: 55, machine_ratio: 5 },
  '劳务工程': { labor_ratio: 95, material_ratio: 3, machine_ratio: 2 },
  '安装工程': { labor_ratio: 50, material_ratio: 40, machine_ratio: 10 },
  '水利工程': { labor_ratio: 10, material_ratio: 40, machine_ratio: 50 },
  '园林工程': { labor_ratio: 40, material_ratio: 50, machine_ratio: 10 },
}

const lmrComparison = computed(() => {
  const ref = lmrReference[projectType.value] || lmrReference['房建工程']
  const structure = costDetail.value?.cost_structure || []
  
  const getRatio = (name) => {
    const item = structure.find(s => s.name.includes(name))
    return item ? item.ratio : 0
  }

  return [
    {
      name: '人工费',
      project_ratio: getRatio('人工'),
      reference_ratio: ref.labor_ratio,
      diff: getRatio('人工') - ref.labor_ratio,
    },
    {
      name: '材料费',
      project_ratio: getRatio('材料'),
      reference_ratio: ref.material_ratio,
      diff: getRatio('材料') - ref.material_ratio,
    },
    {
      name: '机械费',
      project_ratio: getRatio('机械'),
      reference_ratio: ref.machine_ratio,
      diff: getRatio('机械') - ref.machine_ratio,
    },
  ]
})

function statusType(status) {
  const map = {
    ongoing: 'primary',
    completed: 'success',
    pending: 'info',
    settled: 'success',
  }
  return map[status] || 'info'
}

function statusText(status) {
  const map = {
    ongoing: '施工中',
    completed: '已完工',
    pending: '待开工',
    settled: '已结算',
  }
  return map[status] || status
}

function getCostColor(name) {
  if (name.includes('人工')) return '#409eff'
  if (name.includes('材料')) return '#67c23a'
  if (name.includes('机械')) return '#e6a23c'
  return '#909399'
}

function formatMoney(val) {
  if (val === undefined || val === null) return '0.00'
  const num = parseFloat(val)
  if (Math.abs(num) >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function loadDetail() {
  // 加载模拟数据
  const projectData = {
    project_basic: {
      project_id: projectId.value,
      project_name: '苏州工业园区科技园区办公楼项目',
      customer_name: '苏州科技发展有限公司',
      contract_amount: 58000000,
      budget_cost: 49300000,
      status: 'ongoing',
      manager: '王经理',
      start_date: '2026-03-15',
      end_date: '2027-09-30',
    },
    cost_detail: {
      incurred_cost: 4930000,
      carryover_cost: 4930000,
      cost_structure: [
        { name: '人工费', value: 1479000, ratio: 30.0 },
        { name: '材料费', value: 2958000, ratio: 60.0 },
        { name: '机械费', value: 493000, ratio: 10.0 },
      ],
      gross_profit: 870000,
      gross_profit_rate: 15.0,
    },
    gross_profit: {
      amount: 870000,
      rate: 15.0,
      expected_rate: 15.0,
    },
    fund_info: {
      received_amount: 4500000,
      pending_receive: 1300000,
      paid_amount: 2000000,
      pending_pay: 2930000,
      net_cash_flow: 2500000,
    },
    invoice_info: {
      output: {
        amount_with_tax: 5800000,
        amount_no_tax: 5321100.92,
        tax: 478899.08,
      },
      input: {
        estimated_amount_with_tax: 3000000,
        estimated_tax: 180000,
      },
      missing_invoice: {
        missing_input_tax: 120000,
        warning: true,
      },
      tax_burden: {
        vat_burden: 5.6,
        industry_reference: 2.5,
        is_high: true,
        is_low: false,
      }
    },
    construction_settlement: {
      construction_balance: 4930000,
      settlement_balance: 5800000,
      offset_status: '已结算未完工',
      offset_amount: 870000,
    }
  }

  projectInfo.value = projectData.project_basic
  costDetail.value = projectData.cost_detail
  grossProfit.value = projectData.gross_profit
  fundInfo.value = projectData.fund_info
  invoiceInfo.value = projectData.invoice_info
  constructionSettlement.value = projectData.construction_settlement

  nextTick(() => {
    renderCostChart()
  })
}

function renderCostChart() {
  if (!costChart.value || !costDetail.value) return

  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(costChart.value)

  const data = costDetail.value.cost_structure.map((item, index) => ({
    name: item.name,
    value: item.value,
    itemStyle: {
      color: ['#409eff', '#67c23a', '#e6a23c', '#909399'][index]
    }
  }))

  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          fontSize: 12,
        },
        data: data,
      }
    ]
  })
}

function goBack() {
  router.push('/project-board')
}

function handleResize() {
  chartInstance?.resize()
}

watch(activeTab, (tab) => {
  if (tab === 'cost') {
    nextTick(() => renderCostChart())
  }
})

onMounted(() => {
  loadDetail()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.project-detail-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-text {
  font-size: 22px;
  font-weight: bold;
  color: #0a1f44;
}

.top-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.basic-info-card {
  flex: 0 0 400px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #0a1f44;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  color: #909399;
}

.info-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.kpi-cards {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-top: 3px solid #dcdfe6;
}

.kpi-card.income {
  border-top-color: #67c23a;
}

.kpi-card.cost {
  border-top-color: #e6a23c;
}

.kpi-card.profit {
  border-top-color: #c9a24a;
}

.kpi-card.cash {
  border-top-color: #409eff;
}

.kpi-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 22px;
  font-weight: bold;
  color: #0a1f44;
  margin-bottom: 4px;
}

.kpi-value.positive {
  color: #67c23a;
}

.kpi-value.negative {
  color: #f56c6c;
}

.kpi-sub {
  font-size: 12px;
  color: #909399;
}

.detail-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.tab-content {
  padding: 20px 0;
}

.cost-structure-card {
  margin-bottom: 20px;
}

.cost-chart-row {
  display: flex;
  gap: 30px;
  align-items: center;
}

.cost-list {
  flex: 1;
}

.cost-item {
  margin-bottom: 16px;
}

.cost-item:last-child {
  margin-bottom: 0;
}

.cost-item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.cost-name {
  font-size: 14px;
  color: #606266;
}

.cost-amount {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.cost-ratio {
  font-size: 12px;
  color: #909399;
  text-align: right;
  margin-top: 4px;
}

.lmr-compare-card {
  background: #fafafa;
  border-radius: 6px;
  padding: 16px;
}

.compare-table {
  margin-top: 12px;
}

.compare-header {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 8px 12px;
  background: #f0f2f5;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.compare-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
  font-size: 14px;
}

.compare-row:last-child {
  border-bottom: none;
}

.row-name {
  font-weight: 500;
}

.compare-row .high {
  color: #f56c6c;
}

.compare-row .low {
  color: #67c23a;
}

.fund-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.fund-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.fund-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.fund-card.receive .fund-icon {
  background: #f0f9eb;
  color: #67c23a;
}

.fund-card.pending-receive .fund-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.fund-card.pay .fund-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.fund-card.pending-pay .fund-icon {
  background: #ecf5ff;
  color: #409eff;
}

.fund-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 4px;
}

.fund-amount {
  font-size: 20px;
  font-weight: bold;
  color: #303133;
}

.fund-summary-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
}

.fund-analysis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.analysis-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
}

.analysis-item .label {
  color: #909399;
  font-size: 14px;
}

.analysis-item .value {
  font-weight: 600;
  color: #0a1f44;
}

.invoice-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.invoice-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 24px;
  border-left: 4px solid;
}

.invoice-card.output {
  border-left-color: #e6a23c;
}

.invoice-card.input {
  border-left-color: #67c23a;
}

.invoice-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.invoice-amount {
  font-size: 24px;
  font-weight: bold;
  color: #0a1f44;
  margin-bottom: 8px;
}

.invoice-sub {
  font-size: 12px;
  color: #909399;
}

.tax-burden-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.burden-item {
  margin-bottom: 20px;
}

.burden-item:last-child {
  margin-bottom: 0;
}

.burden-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.burden-value {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}

.burden-value .current {
  font-size: 24px;
  font-weight: bold;
  color: #0a1f44;
}

.burden-value .reference {
  font-size: 13px;
  color: #909399;
}

.settlement-card {
  background: #fafafa;
  border-radius: 8px;
  padding: 24px;
}

.settlement-data {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.settlement-item {
  flex: 1;
  text-align: center;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
}

.settlement-item.result {
  background: linear-gradient(135deg, #0a1f44, #1a3a6b);
  color: #fff;
}

.settlement-item.result.unsettled {
  background: linear-gradient(135deg, #e6a23c, #d49442);
}

.settlement-item.result.oversettled {
  background: linear-gradient(135deg, #409eff, #337ecc);
}

.settlement-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.settlement-item.result .settlement-label {
  color: rgba(255, 255, 255, 0.9);
}

.settlement-value {
  font-size: 22px;
  font-weight: bold;
  color: #0a1f44;
  margin-bottom: 4px;
}

.settlement-item.result .settlement-value {
  color: #fff;
}

.settlement-sub {
  font-size: 12px;
  color: #909399;
}

.settlement-item.result .settlement-sub {
  color: rgba(255, 255, 255, 0.8);
}

.settlement-arrow {
  font-size: 24px;
  color: #c9a24a;
  font-weight: bold;
}
</style>
