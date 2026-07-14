<template>
  <div>
    <div class="page-title">银行账户管理</div>
    <div class="chart-card">
      <div class="filter-bar">
        <el-input v-model="keyword" placeholder="搜索账户名称/开户行" style="width: 280px" clearable />
        <el-button type="primary">新增账户</el-button>
      </div>

      <el-table :data="filteredList" style="width: 100%" stripe>
        <el-table-column prop="account_name" label="账户名称" min-width="150" />
        <el-table-column prop="bank_name" label="开户行" min-width="180" />
        <el-table-column prop="account_no" label="账号" width="220" />
        <el-table-column label="账户类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.account_type === 'basic'" type="primary" size="small">基本户</el-tag>
            <el-tag v-else size="small">一般户</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_balance" label="当前余额" width="160" align="right" :formatter="fmtMoney" />
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
import { getBankAccounts } from '@/api/config'

const keyword = ref('')
const bankAccountList = ref([])

const filteredList = computed(() => {
  if (!keyword.value) return bankAccountList.value
  const kw = keyword.value.toLowerCase()
  return bankAccountList.value.filter(
    (item) =>
      item.account_name?.toLowerCase().includes(kw) ||
      item.bank_name?.toLowerCase().includes(kw) ||
      item.account_no?.includes(kw)
  )
})

async function loadBankAccounts() {
  try {
    const data = await getBankAccounts()
    if (data) bankAccountList.value = data.items || []
  } catch (e) {
    console.error('Load bank accounts error:', e)
    loadMockBankAccounts()
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

function loadMockBankAccounts() {
  bankAccountList.value = [
    {
      id: 1,
      account_name: '工行基本户',
      bank_name: '工商银行苏州分行',
      account_no: '1102023456789012345',
      account_type: 'basic',
      current_balance: 8520000
    },
    {
      id: 2,
      account_name: '建行一般户',
      bank_name: '建设银行姑苏支行',
      account_no: '3220198765432109876',
      account_type: 'general',
      current_balance: 3210000
    },
    {
      id: 3,
      account_name: '农行保证金户',
      bank_name: '农业银行园区支行',
      account_no: '1055012345678901234',
      account_type: 'general',
      current_balance: 1500000
    },
    {
      id: 4,
      account_name: '中行贷款专户',
      bank_name: '中国银行苏州分行',
      account_no: '1008600123456789012',
      account_type: 'general',
      current_balance: 0
    }
  ]
}

onMounted(() => {
  loadBankAccounts()
})
</script>
