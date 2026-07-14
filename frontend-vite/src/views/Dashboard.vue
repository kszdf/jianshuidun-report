<template>
  <div>
    <div class="page-title">经营驾驶舱</div>
    <div class="page-subtitle">
      <el-date-picker
        v-model="dashboardPeriod"
        type="month"
        placeholder="选择月份"
        size="small"
        style="width: 140px"
        @change="loadDashboard"
      />
      <span style="margin-left: 12px">数据更新时间：{{ dashboardData ? '实时计算' : '--' }}</span>
    </div>

    <!-- KPI卡片 -->
    <div class="kpi-cards">
      <div class="kpi-card" v-for="ind in dashboardIndicators" :key="ind.key">
        <div class="kpi-label">
          <span>{{ ind.name }}</span>
          <div class="kpi-icon" :class="'icon-' + ind.colorType">
            <el-icon><component :is="ind.icon" /></el-icon>
          </div>
        </div>
        <div class="kpi-value">{{ formatMoney(ind.value) }}</div>
        <div class="kpi-trend" :class="ind.trend_type === 'up' ? 'trend-up' : 'trend-down'">
          {{ ind.trend_type === 'up' ? '↑' : '↓' }} {{ Math.abs(ind.trend) }}%
          <span v-if="ind.suffix" style="color: #909399; margin-left: 8px">{{ ind.suffix }}</span>
        </div>
      </div>
    </div>

    <!-- 趋势图 -->
    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">月度收支趋势</div>
        <div class="chart-box" ref="trendChart"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">应收账龄分布</div>
        <div class="chart-box" ref="agingChart"></div>
      </div>
    </div>

    <!-- 项目排行 + 预警 -->
    <div class="chart-row">
      <div class="chart-card">
        <div class="chart-title">项目利润排行 TOP5</div>
        <div class="chart-box" ref="projectChart"></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">风险预警</div>
        <el-empty v-if="!dashboardWarnings.length" description="暂无预警" :image-size="80" />
        <div v-else>
          <div
            v-for="(w, i) in dashboardWarnings"
            :key="i"
            style="padding: 12px 0; border-bottom: 1px solid #f0f0f0"
          >
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px">
              <el-tag :type="w.level === 'danger' ? 'danger' : 'warning'" size="small">{{
                w.type
              }}</el-tag>
              <span style="font-size: 13px; color: #303133">{{ w.message }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { getDashboard } from '@/api/report'

const dashboardPeriod = ref('')
const dashboardData = ref(null)
const trendChart = ref(null)
const agingChart = ref(null)
const projectChart = ref(null)

let trendChartInstance = null
let agingChartInstance = null
let projectChartInstance = null

const dashboardIndicators = computed(() => {
  if (!dashboardData.value) return []
  const icons = {
    cash: 'Wallet',
    ar: 'Money',
    ap: 'Wallet',
    income: 'Top',
    cost: 'Bottom',
    profit: 'TrendCharts',
    projects: 'Briefcase'
  }
  const colors = {
    cash: 'blue',
    ar: 'orange',
    ap: 'purple',
    income: 'green',
    cost: 'red',
    profit: 'blue',
    projects: 'green'
  }
  return dashboardData.value.indicators.map((ind) => ({
    ...ind,
    icon: icons[ind.key] || 'DataAnalysis',
    colorType: colors[ind.key] || 'blue'
  }))
})

const dashboardWarnings = computed(() => {
  return dashboardData.value?.warnings || []
})

async function loadDashboard() {
  try {
    const data = await getDashboard(dashboardPeriod.value || undefined)
    if (data) {
      dashboardData.value = data
      renderCharts()
    }
  } catch (e) {
    console.error('Load dashboard error:', e)
    // 加载模拟数据
    loadMockDashboard()
  }
}

function renderCharts() {
  if (!dashboardData.value) return
  nextTick(() => {
    // 收支趋势图
    if (trendChart.value) {
      if (trendChartInstance) trendChartInstance.dispose()
      trendChartInstance = echarts.init(trendChart.value)
      const trends = dashboardData.value.trends.income_cost
      trendChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['收入', '成本'], right: 20 },
        grid: { left: 50, right: 20, top: 40, bottom: 30 },
        xAxis: { type: 'category', data: trends.months },
        yAxis: {
          type: 'value',
          axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万' }
        },
        series: [
          {
            name: '收入',
            type: 'line',
            smooth: true,
            data: trends.income,
            itemStyle: { color: '#67c23a' },
            areaStyle: { opacity: 0.1 }
          },
          {
            name: '成本',
            type: 'line',
            smooth: true,
            data: trends.cost,
            itemStyle: { color: '#f56c6c' },
            areaStyle: { opacity: 0.1 }
          }
        ]
      })
    }
    // 账龄饼图
    if (agingChart.value) {
      if (agingChartInstance) agingChartInstance.dispose()
      agingChartInstance = echarts.init(agingChart.value)
      const aging = dashboardData.value.trends.ar_aging
      agingChartInstance.setOption({
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [
          {
            type: 'pie',
            radius: ['45%', '70%'],
            avoidLabelOverlap: true,
            label: { show: true, formatter: '{b}\n{d}%' },
            data: aging,
            color: ['#67c23a', '#e6a23c', '#f56c6c', '#909399']
          }
        ]
      })
    }
    // 项目排行
    if (projectChart.value) {
      if (projectChartInstance) projectChartInstance.dispose()
      projectChartInstance = echarts.init(projectChart.value)
      const projects = dashboardData.value.trends.project_top5 || []
      projectChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 140, right: 60, top: 10, bottom: 30 },
        xAxis: {
          type: 'value',
          axisLabel: { formatter: (v) => (v / 10000).toFixed(0) + '万' }
        },
        yAxis: {
          type: 'category',
          data: projects.map((p) => p.project_name.substring(0, 12) + '...').reverse()
        },
        series: [
          {
            type: 'bar',
            data: projects.map((p) => p.profit).reverse(),
            itemStyle: {
              color: (params) => (params.value >= 0 ? '#67c23a' : '#f56c6c'),
              borderRadius: [0, 4, 4, 0]
            },
            label: {
              show: true,
              position: 'right',
              formatter: (p) => (p.value / 10000).toFixed(1) + '万'
            }
          }
        ]
      })
    }
  })
}

function formatMoney(val) {
  if (val === undefined || val === null) return '0.00'
  const num = parseFloat(val)
  if (Math.abs(num) >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 模拟数据
function loadMockDashboard() {
  dashboardData.value = {
    period: '2026-07',
    indicators: [
      { key: 'cash', name: '在手资金', value: 13280000, unit: '元', trend: 5.2, trend_type: 'up' },
      { key: 'ar', name: '应收账款', value: 28500000, unit: '元', trend: 3.8, trend_type: 'up' },
      { key: 'ap', name: '应付账款', value: 18600000, unit: '元', trend: 2.1, trend_type: 'up' },
      { key: 'income', name: '本月收入', value: 12500000, unit: '元', trend: 15.3, trend_type: 'up' },
      { key: 'cost', name: '本月成本', value: 9800000, unit: '元', trend: 12.1, trend_type: 'up' },
      {
        key: 'profit',
        name: '本月利润',
        value: 2700000,
        unit: '元',
        trend: 21.6,
        trend_type: 'up',
        suffix: '利润率 21.6%'
      },
      { key: 'projects', name: '在手项目', value: 5, unit: '个', trend: 0, trend_type: 'up' }
    ],
    trends: {
      income_cost: {
        months: ['2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07'],
        income: [8200000, 9500000, 10800000, 11200000, 10500000, 12500000],
        cost: [6800000, 7600000, 8500000, 9000000, 8200000, 9800000]
      },
      project_top5: [
        { project_name: '苏州工业园区科技园区办公楼项目', profit: 3200000 },
        { project_name: '相城区人才公寓二期工程', profit: 1800000 },
        { project_name: '高新区标准厂房建设项目', profit: 1500000 },
        { project_name: '吴中区市政道路改造项目', profit: 960000 },
        { project_name: '姑苏区古建筑修缮工程', profit: 450000 }
      ],
      ar_aging: [
        { name: '30天以内', value: 9500000 },
        { name: '30-90天', value: 12000000 },
        { name: '90-180天', value: 5000000 },
        { name: '180天以上', value: 2000000 }
      ]
    },
    warnings: [
      {
        level: 'warning',
        type: '资金紧张',
        message: '在手资金不足半月支出，建议关注现金流',
        count: 1
      }
    ]
  }
  renderCharts()
}

// 窗口 resize 时重绘图表
function handleResize() {
  trendChartInstance?.resize()
  agingChartInstance?.resize()
  projectChartInstance?.resize()
}

onMounted(() => {
  loadDashboard()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChartInstance?.dispose()
  agingChartInstance?.dispose()
  projectChartInstance?.dispose()
})
</script>
