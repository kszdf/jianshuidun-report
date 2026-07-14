<template>
  <div>
    <div class="page-title">项目档案</div>
    <div class="chart-card">
      <div class="filter-bar">
        <el-input
          v-model="projectKeyword"
          placeholder="搜索项目名称"
          style="width: 240px"
          clearable
        />
        <el-select v-model="projectStatusFilter" placeholder="项目状态" style="width: 140px" clearable>
          <el-option label="施工中" value="ongoing" />
          <el-option label="已完工" value="completed" />
          <el-option label="待开工" value="pending" />
        </el-select>
        <el-button type="primary">新增项目</el-button>
      </div>

      <el-table :data="filteredProjectList" style="width: 100%" stripe>
        <el-table-column prop="project_code" label="项目编码" width="140" />
        <el-table-column prop="project_name" label="项目名称" min-width="240" />
        <el-table-column prop="contract_amount" label="合同金额" width="140" align="right" :formatter="fmtMoney" />
        <el-table-column prop="project_manager" label="项目经理" width="120" />
        <el-table-column prop="start_date" label="开工日期" width="120" align="center" />
        <el-table-column prop="end_date" label="竣工日期" width="120" align="center" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'ongoing'" type="primary" size="small">施工中</el-tag>
            <el-tag v-else-if="row.status === 'completed'" type="success" size="small">已完工</el-tag>
            <el-tag v-else type="info" size="small">待开工</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small">编辑</el-button>
            <el-button type="danger" link size="small">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getProjects } from '@/api/config'

const projectKeyword = ref('')
const projectStatusFilter = ref('')
const projectArchiveList = ref([])

const filteredProjectList = computed(() => {
  let list = projectArchiveList.value
  if (projectStatusFilter.value) {
    list = list.filter((p) => p.status === projectStatusFilter.value)
  }
  if (projectKeyword.value) {
    const kw = projectKeyword.value.toLowerCase()
    list = list.filter((p) => p.project_name.toLowerCase().includes(kw))
  }
  return list
})

async function loadProjects() {
  try {
    const data = await getProjects()
    if (data) projectArchiveList.value = data.items || []
  } catch (e) {
    console.error('Load projects error:', e)
    loadMockProjects()
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

function loadMockProjects() {
  projectArchiveList.value = [
    {
      project_code: 'XM2026001',
      project_name: '苏州工业园区科技园区办公楼项目',
      contract_amount: 58000000,
      project_manager: '张工',
      start_date: '2025-03-15',
      end_date: '2026-12-30',
      status: 'ongoing'
    },
    {
      project_code: 'XM2026002',
      project_name: '相城区人才公寓二期工程',
      contract_amount: 32000000,
      project_manager: '李工',
      start_date: '2025-06-01',
      end_date: '2026-09-30',
      status: 'ongoing'
    },
    {
      project_code: 'XM2026003',
      project_name: '高新区标准厂房建设项目',
      contract_amount: 45000000,
      project_manager: '王工',
      start_date: '2026-08-01',
      end_date: '2027-06-30',
      status: 'pending'
    },
    {
      project_code: 'XM2025001',
      project_name: '吴中区市政道路改造项目',
      contract_amount: 15600000,
      project_manager: '赵工',
      start_date: '2025-04-01',
      end_date: '2026-06-30',
      status: 'ongoing'
    },
    {
      project_code: 'XM2024005',
      project_name: '姑苏区古建筑修缮工程',
      contract_amount: 8900000,
      project_manager: '陈工',
      start_date: '2024-09-01',
      end_date: '2025-12-31',
      status: 'completed'
    }
  ]
}

onMounted(() => {
  loadProjects()
})
</script>
