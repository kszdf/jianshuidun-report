<template>
  <div>
    <div class="page-title">资金日报</div>
    <div class="filter-bar">
      <el-date-picker
        v-model="cashDate"
        type="date"
        placeholder="选择日期"
        size="default"
        style="width: 180px"
        @change="loadCashDaily"
      />
      <el-button type="primary" @click="loadCashDaily">查询</el-button>
    </div>

    <div class="kpi-cards">
      <div class="kpi-card">
        <div class="kpi-label">
          <span>资金总余额</span>
          <div class="kpi-icon icon-blue"><el-icon><Wallet /></el-icon></div>
        </div>
        <div class="kpi-value">{{ formatMoney(cashData.total_balance) }}</div>
        <div class="kpi-trend" style="color: #909399">截至 {{ cashData.report_date }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">
          <span>当日收入</span>
          <div class="kpi-icon icon-green"><el-icon><Top /></el-icon></div>
        </div>
        <div class="kpi-value" style="color: #67c23a">+{{ formatMoney(cashData.daily_income) }}</div>
        <div class="kpi-trend" style="color: #909399">本日流入</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">
          <span>当日支出</span>
          <div class="kpi-icon icon-red"><el-icon><Bottom /></el-icon></div>
        </div>
        <div class="kpi-value" style="color: #f56c6c">-{{ formatMoney(cashData.daily_expense) }}</div>
        <div class="kpi-trend" style="color: #909399">本日流出</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">
          <span>当日净额</span>
          <div class="kpi-icon icon-orange"><el-icon><Sort /></el-icon></div>
        </div>
        <div
          class="kpi-value"
          :style="{ color: cashData.net_flow >= 0 ? '#67c23a' : '#f56c6c' }"
        >
          {{ cashData.net_flow >= 0 ? '+' : '' }}{{ formatMoney(cashData.net_flow) }}
        </div>
        <div class="kpi-trend" style="color: #909399">收支差额</div>
      </div>
    </div>

    <div class="chart-card">
      <div class="chart-title">银行账户明细</div>
      <el-table :data="cashData.accounts || []" style="width: 100%" stripe>
        <el-table-column prop="account_name" label="账户名称" min-width="150" />
        <el-table-column prop="bank_name" label="开户行" min-width="180" />
        <el-table-column prop="account_no" label="账号" width="220" />
        <el-table-column label="账户类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.account_type === 'basic'" type="primary" size="small">基本户</el-tag>
            <el-tag v-else-if="row.account_type === 'general'" size="small">一般户</el-tag>
            <el-tag v-else-if="row.account_type === 'private'" type="warning" size="small">私户</el-tag>
            <el-tag v-else size="small">{{ row.account_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="balance" label="当前余额" width="160" align="right" :formatter="fmtMoney">
          <template #header><span style="color: #606266">当前余额(元)</span></template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getCashDaily } from '@/api/report'

const cashDate = ref('')
const cashData = reactive({
  total_balance: 0,
  daily_income: 0,
  daily_expense: 0,
  net_flow: 0,
  accounts: [],
  report_date: ''
})

async function loadCashDaily() {
  try {
    const data = await getCashDaily(cashDate.value || undefined)
    if (data) {
      Object.assign(cashData, data)
    }
  } catch (e) {
    console.error('Load cash daily error:', e)
    loadMockCashDaily()
  }
}

function formatMoney(val) {
  if (val === undefined || val === null) return '0.00'
  const num = parseFloat(val)
  if (Math.abs(num) >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function fmtMoney(row, col, val) {
  return formatMoney(val)
}

function loadMockCashDaily() {
  const today = new Date().toISOString().substring(0, 10)
  Object.assign(cashData, {
    report_date: today,
    total_balance: 13230000,
    daily_income: 2000000,
    daily_expense: 1650000,
    net_flow: 350000,
    accounts: [
      {
        account_name: '工行基本户',
        bank_name: '工商银行苏州分行',
        account_no: '1102023456789012345',
        account_type: 'basic',
        balance: 8520000
      },
      {
        account_name: '建行一般户',
        bank_name: '建设银行姑苏支行',
        account_no: '3220198765432109876',
        account_type: 'general',
        balance: 3210000
      },
      {
        account_name: '农行保证金户',
        bank_name: '农业银行园区支行',
        account_no: '1055012345678901234',
        account_type: 'general',
        balance: 1500000
      }
    ]
  })
}

onMounted(() => {
  loadCashDaily()
})
</script>
