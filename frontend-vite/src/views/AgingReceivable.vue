<template>
  <div>
    <div class="page-title">应收账龄分析</div>
    <div class="filter-bar">
      <el-date-picker
        v-model="arPeriod"
        type="month"
        placeholder="选择月份"
        size="default"
        style="width: 180px"
      />
      <el-button type="primary" @click="loadArAging">查询</el-button>
    </div>

    <div class="kpi-cards">
      <div class="kpi-card">
        <div class="kpi-label">
          <span>应收账款总额</span>
          <div class="kpi-icon icon-blue"><el-icon><Money /></el-icon></div>
        </div>
        <div class="kpi-value">{{ formatMoney(arData.total_ar) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">
          <span>逾期金额</span>
          <div class="kpi-icon icon-red"><el-icon><Warning /></el-icon></div>
        </div>
        <div class="kpi-value" style="color: #f56c6c">{{ formatMoney(arData.overdue_total) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">
          <span>逾期率</span>
          <div class="kpi-icon icon-orange"><el-icon><TrendCharts /></el-icon></div>
        </div>
        <div class="kpi-value">{{ arData.overdue_rate }}%</div>
        <div class="kpi-trend" :class="arData.overdue_rate > 20 ? 'trend-up' : 'trend-down'">
          {{ arData.overdue_rate > 20 ? '偏高' : '正常' }}
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">
          <span>客户数量</span>
          <div class="kpi-icon icon-green"><el-icon><User /></el-icon></div>
        </div>
        <div class="kpi-value">{{ arData.details ? arData.details.length : 0 }}</div>
      </div>
    </div>

    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">账龄分布</div>
        <div class="chart-box" ref="arAgingChart"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">账龄构成</div>
        <div class="chart-box" ref="arPieChart"></div>
      </div>
    </div>

    <div class="chart-card">
      <div class="chart-title">客户明细</div>
      <el-table
        :data="arData.details || []"
        style="width: 100%"
        stripe
        :default-sort="{ prop: 'days', order: 'descending' }"
      >
        <el-table-column prop="customer_name" label="客户名称" min-width="200" />
        <el-table-column
          prop="balance"
          label="应收余额"
          width="140"
          align="right"
          :formatter="fmtMoney"
          sortable
        />
        <el-table-column prop="days" label="账龄(天)" width="100" align="right" sortable />
        <el-table-column prop="last_payment_date" label="最后收款日" width="120" align="center" />
        <el-table-column prop="aging_level" label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.aging_level === 'normal'" type="success" size="small">正常</el-tag>
            <el-tag v-else-if="row.aging_level === 'attention'" type="info" size="small">关注</el-tag>
            <el-tag v-else-if="row.aging_level === 'warning'" type="warning" size="small">预警</el-tag>
            <el-tag v-else type="danger" size="small">危险</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getArAging } from '@/api/report'

const arPeriod = ref('')
const arData = reactive({
  total_ar: 0,
  overdue_total: 0,
  overdue_rate: 0,
  buckets: {},
  details: []
})
const arAgingChart = ref(null)
const arPieChart = ref(null)

let arAgingChartInstance = null
let arPieChartInstance = null

async function loadArAging() {
  try {
    const data = await getArAging(arPeriod.value || undefined)
    if (data) {
      Object.assign(arData, data)
      nextTick(() => renderArCharts())
    }
  } catch (e) {
    console.error('Load ar aging error:', e)
    loadMockArAging()
  }
}

function renderArCharts() {
  const buckets = arData.buckets || {}
  const labels = ['30天内', '30-90天', '90-180天', '180天以上']
  const values = [
    buckets.within_30 || 0,
    buckets.between_30_90 || 0,
    buckets.between_90_180 || 0,
    buckets.over_180 || 0
  ]

  if (arAgingChart.value) {
    if (arAgingChartInstance) arAgingChartInstance.dispose()
    arAgingChartInstance = echarts.init(arAgingChart.value)
    arAgingChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 60, right: 20, top: 20, bottom: 40 },
      xAxis: { type: 'category', data: labels },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万' }
      },
      series: [
        {
          type: 'bar',
          data: values,
          barWidth: '50%',
          itemStyle: {
            color: (params) => ['#67c23a', '#e6a23c', '#f56c6c', '#909399'][params.dataIndex],
            borderRadius: [4, 4, 0, 0]
          },
          label: {
            show: true,
            position: 'top',
            formatter: (p) => (p.value / 10000).toFixed(1) + '万'
          }
        }
      ]
    })
  }

  if (arPieChart.value) {
    if (arPieChartInstance) arPieChartInstance.dispose()
    arPieChartInstance = echarts.init(arPieChart.value)
    const pieData = labels
      .map((name, i) => ({ name, value: values[i] }))
      .filter((d) => d.value > 0)
    arPieChartInstance.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: 0 },
      series: [
        {
          type: 'pie',
          radius: ['45%', '70%'],
          data: pieData,
          color: ['#67c23a', '#e6a23c', '#f56c6c', '#909399'],
          label: { formatter: '{b}\n{d}%' }
        }
      ]
    })
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

function loadMockArAging() {
  Object.assign(arData, {
    total_ar: 28500000,
    overdue_total: 7000000,
    overdue_rate: 24.6,
    buckets: {
      within_30: 9500000,
      between_30_90: 12000000,
      between_90_180: 5000000,
      over_180: 2000000
    },
    details: [
      {
        customer_name: '苏州科技发展有限公司',
        balance: 3000000,
        days: 15,
        last_payment_date: '2026-06-25',
        aging_level: 'normal'
      },
      {
        customer_name: '相城城建投资有限公司',
        balance: 2500000,
        days: 45,
        last_payment_date: '2026-05-26',
        aging_level: 'attention'
      },
      {
        customer_name: '吴中区市政公用局',
        balance: 1200000,
        days: 60,
        last_payment_date: '2026-05-11',
        aging_level: 'attention'
      },
      {
        customer_name: '苏州高新产业投资集团',
        balance: 5000000,
        days: 120,
        last_payment_date: '2026-03-12',
        aging_level: 'warning'
      },
      {
        customer_name: '姑苏区文旅局',
        balance: 800000,
        days: 200,
        last_payment_date: '2025-12-22',
        aging_level: 'danger'
      }
    ]
  })
  nextTick(renderArCharts)
}

function handleResize() {
  arAgingChartInstance?.resize()
  arPieChartInstance?.resize()
}

onMounted(() => {
  loadArAging()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  arAgingChartInstance?.dispose()
  arPieChartInstance?.dispose()
})
</script>
