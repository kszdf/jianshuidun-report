<template>
  <div class="project-board-page">
    <div class="page-header">
      <div>
        <div class="page-title">项目独立核算看板</div>
        <div class="page-subtitle">每个项目一本账，老板一眼看清赚不赚钱</div>
      </div>
      <div class="header-tools">
        <!-- 收入模式切换 -->
        <el-radio-group v-model="incomeMode" size="small" @change="loadData">
          <el-radio-button value="invoicing">开票口径</el-radio-button>
          <el-radio-button value="settlement">结算口径</el-radio-button>
          <el-radio-button value="percentage">完工百分比</el-radio-button>
        </el-radio-group>
        <el-date-picker
          v-model="period"
          type="month"
          placeholder="选择月份"
          size="small"
          style="width: 140px; margin-left: 12px"
          @change="loadData"
        />
      </div>
    </div>

    <!-- 汇总卡片 -->
    <div class="summary-cards" v-if="boardData">
      <div class="summary-card">
        <div class="card-label">合同总额</div>
        <div class="card-value">{{ formatMoney(boardData.summary.total_contract) }}</div>
      </div>
      <div class="summary-card income">
        <div class="card-label">累计收入</div>
        <div class="card-value">{{ formatMoney(boardData.summary.total_income) }}</div>
        <div class="card-sub">{{ incomeModeName }}口径</div>
      </div>
      <div class="summary-card cost">
        <div class="card-label">累计成本</div>
        <div class="card-value">{{ formatMoney(boardData.summary.total_cost) }}</div>
      </div>
      <div class="summary-card profit">
        <div class="card-label">累计毛利</div>
        <div class="card-value">{{ formatMoney(boardData.summary.total_profit) }}</div>
        <div class="card-sub">毛利率 {{ boardData.summary.overall_profit_rate }}%</div>
      </div>
      <div class="summary-card cash">
        <div class="card-label">累计收款</div>
        <div class="card-value">{{ formatMoney(boardData.summary.total_received) }}</div>
      </div>
    </div>

    <!-- 项目列表 -->
    <div class="project-list">
      <div
        v-for="project in boardData?.items"
        :key="project.project_id"
        class="project-card"
        @click="goToDetail(project.project_id)"
      >
        <div class="project-header">
          <div class="project-name">{{ project.project_name }}</div>
          <el-tag :type="statusType(project.status)" size="small">
            {{ statusText(project.status) }}
          </el-tag>
        </div>

        <div class="project-info-row">
          <div class="info-item">
            <span class="info-label">合同金额</span>
            <span class="info-value">{{ formatMoney(project.contract_amount) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">完工进度</span>
            <span class="info-value progress-value">
              <el-progress
                :percentage="Math.min(project.progress, 100)"
                :stroke-width="6"
                :show-text="false"
                style="width: 80px; display: inline-block; vertical-align: middle; margin-right: 8px"
              />
              {{ project.progress.toFixed(1) }}%
            </span>
          </div>
        </div>

        <div class="project-metrics">
          <div class="metric">
            <div class="metric-label">已开票</div>
            <div class="metric-value income">{{ formatMoney(project.income_amount) }}</div>
          </div>
          <div class="metric">
            <div class="metric-label">已收款</div>
            <div class="metric-value cash">{{ formatMoney(project.received_amount) }}</div>
          </div>
          <div class="metric">
            <div class="metric-label">待收款</div>
            <div class="metric-value pending">{{ formatMoney(project.pending_receive) }}</div>
          </div>
          <div class="metric">
            <div class="metric-label">已发生成本</div>
            <div class="metric-value cost">{{ formatMoney(project.incurred_cost) }}</div>
          </div>
          <div class="metric">
            <div class="metric-label">毛利</div>
            <div class="metric-value" :class="project.gross_profit >= 0 ? 'profit' : 'loss'">
              {{ formatMoney(project.gross_profit) }}
            </div>
          </div>
          <div class="metric">
            <div class="metric-label">毛利率</div>
            <div class="metric-value" :class="project.gross_profit_rate >= 10 ? 'profit' : 'warning'">
              {{ project.gross_profit_rate.toFixed(1) }}%
            </div>
          </div>
        </div>

        <div class="project-footer">
          <span class="manager">项目经理：{{ project.manager || '-' }}</span>
          <el-button type="primary" link size="small">
            查看详情
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!boardData?.items?.length" description="暂无项目数据" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const period = ref('')
const incomeMode = ref('invoicing')
const boardData = ref(null)

const incomeModeName = computed(() => {
  const map = {
    invoicing: '开票',
    settlement: '结算',
    percentage: '完工百分比'
  }
  return map[incomeMode.value] || '开票'
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
    unknown: '未知',
  }
  return map[status] || status
}

function formatMoney(val) {
  if (val === undefined || val === null) return '0.00'
  const num = parseFloat(val)
  if (Math.abs(num) >= 100000000) return (num / 100000000).toFixed(2) + '亿'
  if (Math.abs(num) >= 10000) return (num / 10000).toFixed(2) + '万'
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

async function loadData() {
  // 加载模拟数据（MVP阶段）
  boardData.value = {
    total: 4,
    items: [
      {
        project_id: 1,
        project_name: '苏州工业园区科技园区办公楼项目',
        project_code: 'XM2026001',
        status: 'ongoing',
        contract_amount: 58000000,
        income_amount: 18500000,
        received_amount: 14200000,
        pending_receive: 4300000,
        incurred_cost: 15725000,
        carryover_cost: 15725000,
        gross_profit: 2775000,
        gross_profit_rate: 15.0,
        progress: 31.9,
        manager: '王经理',
      },
      {
        project_id: 2,
        project_name: '吴中区市政道路改造项目',
        project_code: 'XM2026002',
        status: 'ongoing',
        contract_amount: 15600000,
        income_amount: 7200000,
        received_amount: 5800000,
        pending_receive: 1400000,
        incurred_cost: 6120000,
        carryover_cost: 6120000,
        gross_profit: 1080000,
        gross_profit_rate: 15.0,
        progress: 46.2,
        manager: '陈工',
      },
      {
        project_id: 3,
        project_name: '高新区产业园精装修工程',
        project_code: 'XM2026003',
        status: 'ongoing',
        contract_amount: 8600000,
        income_amount: 3600000,
        received_amount: 2900000,
        pending_receive: 700000,
        incurred_cost: 3060000,
        carryover_cost: 3060000,
        gross_profit: 540000,
        gross_profit_rate: 15.0,
        progress: 41.9,
        manager: '刘工',
      },
      {
        project_id: 4,
        project_name: '相城区人才公寓一期工程',
        project_code: 'XM2026004',
        status: 'completed',
        contract_amount: 32000000,
        income_amount: 32000000,
        received_amount: 30400000,
        pending_receive: 1600000,
        incurred_cost: 27200000,
        carryover_cost: 27200000,
        gross_profit: 4800000,
        gross_profit_rate: 15.0,
        progress: 100,
        manager: '赵经理',
      },
    ],
    summary: {
      total_contract: 114200000,
      total_income: 61300000,
      total_cost: 52105000,
      total_profit: 9195000,
      total_received: 53300000,
      overall_profit_rate: 15.0,
    }
  }
}

function goToDetail(projectId) {
  router.push(`/project-board/detail/${projectId}`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.project-board-page {
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

.header-tools {
  display: flex;
  align-items: center;
}

.summary-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.summary-card {
  flex: 1;
  background: linear-gradient(135deg, #ffffff 0%, #f5f7fa 100%);
  border-radius: 8px;
  padding: 20px;
  border-left: 4px solid #dcdfe6;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.summary-card.income {
  border-left-color: #67c23a;
}

.summary-card.cost {
  border-left-color: #e6a23c;
}

.summary-card.profit {
  border-left-color: #c9a24a;
}

.summary-card.cash {
  border-left-color: #409eff;
}

.card-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: #0a1f44;
}

.summary-card.income .card-value {
  color: #67c23a;
}

.summary-card.cost .card-value {
  color: #e6a23c;
}

.summary-card.profit .card-value {
  color: #c9a24a;
}

.summary-card.cash .card-value {
  color: #409eff;
}

.card-sub {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.project-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.project-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid transparent;
}

.project-card:hover {
  box-shadow: 0 4px 16px rgba(10, 31, 68, 0.12);
  border-color: #c9a24a;
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: #0a1f44;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-info-row {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #909399;
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.progress-value {
  display: flex;
  align-items: center;
}

.project-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.metric {
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.metric-value.income {
  color: #67c23a;
}

.metric-value.cost {
  color: #e6a23c;
}

.metric-value.profit {
  color: #c9a24a;
}

.metric-value.loss {
  color: #f56c6c;
}

.metric-value.warning {
  color: #e6a23c;
}

.metric-value.cash {
  color: #409eff;
}

.metric-value.pending {
  color: #909399;
}

.project-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.manager {
  font-size: 12px;
  color: #909399;
}
</style>
