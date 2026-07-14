<template>
  <div>
    <div class="page-title">项目利润表</div>
    <div class="filter-bar">
      <el-date-picker
        v-model="profitPeriod"
        type="month"
        placeholder="选择月份(不选则本年累计)"
        size="default"
        style="width: 200px"
        clearable
      />
      <el-button type="primary" @click="loadProjectProfit">查询</el-button>
      <el-button @click="exportProfit">导出Excel</el-button>
      <span style="margin-left: auto; color: #909399; font-size: 13px"
        >共 {{ projectList.length }} 个项目</span
      >
    </div>
    <el-table
      :data="projectList"
      style="width: 100%"
      stripe
      :default-sort="{ prop: 'profit', order: 'descending' }"
    >
      <el-table-column prop="project_name" label="项目名称" min-width="240" />
      <el-table-column prop="contract_amount" label="合同金额" width="140" align="right" :formatter="fmtMoney">
        <template #header><span style="color: #606266">合同金额</span></template>
      </el-table-column>
      <el-table-column prop="income" label="累计收入" width="140" align="right" :formatter="fmtMoney" sortable />
      <el-table-column prop="cost" label="累计成本" width="140" align="right" :formatter="fmtMoney" sortable />
      <el-table-column prop="profit" label="累计利润" width="140" align="right" :formatter="fmtMoney" sortable />
      <el-table-column prop="profit_rate" label="利润率" width="100" align="right" sortable>
        <template #default="{ row }">
          <span
            :style="{
              color: row.profit_rate >= 15 ? '#67c23a' : row.profit_rate >= 8 ? '#e6a23c' : '#f56c6c'
            }"
            >{{ row.profit_rate }}%</span
          >
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.status === 'ongoing'" type="primary" size="small">施工中</el-tag>
          <el-tag v-else-if="row.status === 'completed'" type="success" size="small">已完工</el-tag>
          <el-tag v-else-if="row.status === 'pending'" type="info" size="small">待开工</el-tag>
          <el-tag v-else size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" align="center">
        <template #default="{ row }">
          <el-button type="primary" link @click="viewProjectDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getProjectProfit } from '@/api/report'

const profitPeriod = ref('')
const projectList = ref([])

async function loadProjectProfit() {
  try {
    const data = await getProjectProfit(profitPeriod.value || undefined)
    if (data) projectList.value = data.items || []
  } catch (e) {
    console.error('Load project profit error:', e)
    loadMockProjectProfit()
  }
}

function viewProjectDetail(row) {
  ElMessage.info('项目详情功能开发中')
}

function exportProfit() {
  ElMessage.info('导出功能开发中')
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

function loadMockProjectProfit() {
  projectList.value = [
    {
      project_name: '苏州工业园区科技园区办公楼项目',
      contract_amount: 58000000,
      income: 28500000,
      cost: 25300000,
      profit: 3200000,
      profit_rate: 11.2,
      status: 'ongoing'
    },
    {
      project_name: '相城区人才公寓二期工程',
      contract_amount: 32000000,
      income: 18200000,
      cost: 16400000,
      profit: 1800000,
      profit_rate: 9.9,
      status: 'ongoing'
    },
    {
      project_name: '高新区标准厂房建设项目',
      contract_amount: 45000000,
      income: 0,
      cost: 0,
      profit: 0,
      profit_rate: 0,
      status: 'pending'
    },
    {
      project_name: '吴中区市政道路改造项目',
      contract_amount: 15600000,
      income: 8500000,
      cost: 7540000,
      profit: 960000,
      profit_rate: 11.3,
      status: 'ongoing'
    },
    {
      project_name: '姑苏区古建筑修缮工程',
      contract_amount: 8900000,
      income: 8900000,
      cost: 8450000,
      profit: 450000,
      profit_rate: 5.1,
      status: 'completed'
    }
  ]
}

onMounted(() => {
  loadProjectProfit()
})
</script>
